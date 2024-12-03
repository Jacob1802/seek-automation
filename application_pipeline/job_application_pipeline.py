from email_sender.email_sender import EmailSender
from utils.utils import generate_cover_letter_pdf
from scrapers.scraper import JobScraper
from agents.agent import AIAgent
from pathlib import Path
from typing import Dict
import logging
import time
import csv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class ApplicationPipeline:
    def __init__(self, run_config: Dict, applied_path: str, smtp_protocol: str):
        self.scraper = JobScraper(run_config)
        self.email_sender = EmailSender(smtp_protocol)
        self.applied_path = Path(applied_path)
        self.applied = self._load_applied_emails()
    
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
            for row in self.applied:
                writer.writerow({'email': row[0], 'id': row[1]})

    def run(self, resume_txt: str, resume_pdf_path: str, cover_letter_path: str, your_name: str, convert_to_australian_language: bool):
        try:
            logging.info("Scraping job listings...")
            job_data = self.scraper.scrape("websift/seek-job-scraper")

            logging.info("Extracting contact information...")
            jobs = [
                job
                for job in job_data if job['contacts']
                for contact in job['contacts'] if contact['type'].lower() == 'email'
            ]
            
            logging.info(f"Found {len(jobs)} jobs with contact information")

            # Process each job and send applications
            for job in jobs:
                try:
                    job_id = job['id']
                    self.agent = AIAgent(your_name)

                    # Skips jobs that don't have an email
                    emails = [email['value'] for email in job['contacts'] if email['type'].lower() == "email"]
                    if not emails:
                        continue
                    
                    applied_emails = [item[0] for item in self.applied]
                    position = job.get('title', '')
                    
                    for email in emails:
                        if email in applied_emails:
                            continue

                        cover_letter = self.agent.prepare_cover_letter(job, resume_txt, email, convert_to_australian_language)
                        msg = self.agent.write_email_contents()

                        generate_cover_letter_pdf(cover_letter, cover_letter_path)

                        success = self.email_sender.send_application(
                            email,
                            job,
                            msg,
                            resume_pdf_path,
                            cover_letter_path
                        )
                        if success:
                            logging.info(f"Successfully processed application to {email} for {position}, {job_id}")
                            self.applied.append([email, job_id])
                        else:
                            raise RuntimeError(f"Email sending failed for job application: {position}, Job ID: {job_id}")

                        
                except Exception as e:
                    logging.error(f"Error processing job application: {e}")
                # Wait 30sec to not overload api can be removed if using official apis
                time.sleep(30)

        except Exception as e:
            logging.error(f"Error {e}")
        finally:
            # Ensure to write all applied jobs if error/keyboard interrupt occurs
            self._write_applied()