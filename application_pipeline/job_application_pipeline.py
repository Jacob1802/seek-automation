
from sentence_transformers import SentenceTransformer
from common.utils import generate_cover_letter_pdf
from email_sender.email_sender import EmailSender
from scipy.spatial.distance import cosine
from scrapers.scraper import JobScraper
from integrations.agent import AIAgent
from pathlib import Path
import logging
import time
import csv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class ApplicationPipeline:
    def __init__(self, run_config, args):
        self.scraper = JobScraper(run_config)
        self.args = args
        self.agent = AIAgent(args.first_name, args.model)
        self.email_sender = EmailSender(args.smtp_protocol)
        self.applied_path = Path(args.applied_path)
        self.applied = self._load_applied_emails()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.encoded_resume_txt = self.model.encode(self.args.resume_txt, convert_to_numpy=True)
    
    def _load_applied_emails(self):
        if not self.applied_path.exists():
            return []

        with self.applied_path.open('r') as file:
            reader = csv.reader(file)
            next(reader)
            # Use a list to preserve the order, as it may be important to track the most recently applied jobs.
            applied = [row for row in reader]

        return applied

    def _write_applied(self):
        # Avoid appending to prevent duplicating existing items when reading.
        with self.applied_path.open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['email', 'id'])
            writer.writeheader()
            writer.writerows([{'email': row[0], 'id': row[1]} for row in self.applied])

    def calculate_resume_jd_similarity(self, jd_text):
        jd_vector = self.model.encode(jd_text, convert_to_numpy=True)
        sim_score = 1 - cosine(self.encoded_resume_txt, jd_vector)

        return sim_score

    def run(self):
        try:
            logging.info("Scraping job listings...")
            job_data = self.scraper.scrape("websift/seek-job-scraper")

            logging.info(f"Found {len(job_data)} jobs with contact information")

            for job in job_data:
                try:
                    job_id = job['id']
                    # Re init agent if using meta ai to avoid limit context window issues
                    if not self.args.use_openai:
                        self.agent = AIAgent(self.args.first_name)
                    
                    applied_emails = [item[0] for item in self.applied]
                    position = job.get('title', '')
                    raw_content = job.get('content', {})
                    job_description = raw_content.get('sections')
                    if not job_description:
                        logging.warning("No job description found")
                        continue
                    
                    score = self.calculate_resume_jd_similarity(" ".join(job_description))
                    if score < 0.4:
                        continue

                    for email in job['emails']:
                        if email in applied_emails:
                            continue

                        cover_letter = self.agent.prepare_cover_letter(job, self.args.resume_txt, email, self.args.australian_language)
                        msg = self.agent.write_email_contents()

                        generate_cover_letter_pdf(cover_letter, self.args.cover_letter_path)

                        success = self.email_sender.send_application(
                            email,
                            job,
                            msg,
                            self.args.resume_pdf_path,
                            self.args.cover_letter_path
                        )
                        if success:
                            logging.info(f"Successfully processed application to {email} for {position}, {job_id}")
                            self.applied.append([email, job_id])
                        else:
                            raise RuntimeError(f"Email sending failed for job application: {position}, Job ID: {job_id}")
                        
                except Exception as e:
                    logging.error(f"Error processing job application: {e}")
                # Wait 30sec to not overload api can be removed if using official apis
                if not self.args.use_openai:
                    logging.info('sleeping')
                    time.sleep(30)

        except Exception as e:
            logging.error(f"Error {e}")
        finally:
            # Ensure to write all applied jobs if error/keyboard interrupt occurs
            self._write_applied()