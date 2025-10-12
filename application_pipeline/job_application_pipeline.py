from sentence_transformers import SentenceTransformer
from common.utils import generate_cover_letter_pdf, load_json_file, write_json_file
from integrations.mail_handler import MailClient
from integrations.seek_client import SeekClient
from scipy.spatial.distance import cosine
from scrapers.scraper import JobScraper
from integrations.agent import AIAgent
from datetime import datetime
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class ApplicationPipeline:
    def __init__(self, run_config, args):
        self.scraper = JobScraper(run_config)
        self.args = args
        self.agent = AIAgent(args.first_name, args.model)
        self.email_sender = MailClient(args.mail_protocol)
        self.applied = self._load_applied(args.applied_path)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.encoded_resume_txt = self.model.encode(self.args.resume_txt, convert_to_numpy=True)

    def _load_applied(self, path):
        applied = load_json_file(path)
        if not applied:
            return {'jobs': {}, 'email_history': {}}
        
        return applied

    def calculate_resume_jd_similarity(self, jd_text):
        jd_vector = self.model.encode(jd_text, convert_to_numpy=True)
        sim_score = 1 - cosine(self.encoded_resume_txt, jd_vector)

        return sim_score

    def should_skip_email(self, email):
        if email in self.applied['email_history']:
            last_contacted = datetime.fromisoformat(self.applied['email_history'][email]['last_contacted'])
            days_since_contact = (datetime.now() - last_contacted).days
            if days_since_contact < 7:
                logging.info(f"Recently contacted {email} {days_since_contact} days ago, skipping.")    
                return True
        return False

    async def run(self):
        logging.info("Scraping job listings...")
        job_data = self.scraper.scrape("websift/seek-job-scraper")
        logging.info(f"Found {len(job_data)} jobs with contact information")
        if not job_data:
            logging.info("No jobs found, exiting.")
            return
        
        with SeekClient(self.args.mail_protocol) as seek_client:
            seek_client.login()

            for job in job_data:
                try:
                    job_id = job['id']
                    if job_id in self.applied['jobs']:
                        logging.info(f"Already applied to job {job_id}, skipping.")
                        continue
                    # Re init agent if using meta ai to avoid limit context window issues
                    if not self.args.use_openai:
                        self.agent = AIAgent(self.args.first_name)
                    
                    position = job.get('title', '')
                    raw_content = job.get('content', {})
                    job_description = raw_content.get('sections')
                    if not job_description:
                        logging.warning("No job description found")
                        continue
                    
                    score = self.calculate_resume_jd_similarity(" ".join(job_description))
                    if score < 0.4:
                        continue
                    
                    seek_success = False
                    email_success = False
                    emails_contacted = []

                    cover_letter = self.agent.prepare_cover_letter(job, self.args.resume_txt, self.args.australian_language)
                    generate_cover_letter_pdf(cover_letter, self.args.cover_letter_path)

                    # Skip over jobs that require questions to be answered
                    if not job['hasRoleRequirements']:
                        success = seek_client.apply(job_id, resume_path=self.args.resume_pdf_path, cover_letter_path=self.args.cover_letter_path)
                        if success:
                            logging.info(f"successfully applied to job {job_id} via seek")
                            seek_success = True

                        
                    for email in job['emails']:
                        if self.should_skip_email(email):
                            continue

                        msg = self.agent.write_email_contents()

                        success = self.email_sender.send_application(
                            email,
                            job,
                            msg,
                            self.args.resume_pdf_path,
                            self.args.cover_letter_path
                        )
                        if success:
                            logging.info(f"Successfully processed application to {email} for {position}, {job_id}")
                            email_success = True
                            emails_contacted.append(email)
                            if email in self.applied['email_history']:
                                self.applied['email_history'][email]['last_contacted'] = datetime.now().isoformat()
                                self.applied['email_history'][email]['jobs_contacted'].append(job_id)
                            else:
                                self.applied['email_history'][email] = {
                                    'last_contacted': datetime.now().isoformat(),
                                    'jobs_contacted': [job_id]
                                }
                    
                    self.applied['jobs'][job_id] = {
                        'applied_on': datetime.now().isoformat(),
                        'similarity_score': score,
                        'applied_via_seek': seek_success,
                        'applied_via_email': email_success,
                        'emails_contacted': emails_contacted,
                        'position': position,
                        'link': job.get('link', '')
                    }

                    write_json_file(self.args.applied_path, self.applied)
                except Exception as e:
                    logging.error(f"Error processing job application: {e}")

                # Wait 30sec to not overload api can be removed if using official apis
                if not self.args.use_openai:
                    logging.info('sleeping')
                    time.sleep(30)