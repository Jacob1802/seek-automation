from email.mime.multipart import MIMEMultipart
from utils import generate_cover_letter_pdf
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from apify_client import ApifyClient
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from meta_ai_api import MetaAI
from email import encoders
import smtplib
import time
import sys
import csv
import os
import re

load_dotenv()

# Add your first name here
YOUR_NAME = ""
assert YOUR_NAME != ""
assert os.path.exists("resume.txt")
assert os.path.exists("resume.pdf")

class JobScraper:
    def __init__(self, run_config: Dict):
        self.run_config = run_config
        self.client = ApifyClient(os.getenv("APIFY_KEY"))
        
    def scrape(self) -> List[Dict]:
        """Scrape job listings and return the data"""
        run = self.client.actor("websift/seek-job-scraper").call(run_input=self.run_config)
        return self.get_dataset(run)
    
    def get_dataset(self, run: Dict) -> List[Dict]:
        """Retrieve and return the dataset from the scraping run"""
        data = self.client.dataset(run["defaultDatasetId"]).list_items().items
        return data

class AIAgent:
    def __init__(self):
        self.llm = MetaAI()
    
    def prepare_cover_letter(self, job_data: Dict, resume: str, email: str) -> str:
        """Generate and review cover letter"""
        job_description = job_data.get('content', '').get('sections', '')
        position = job_data.get('title', 'Unknown position')
        company_name = job_data.get('companyProfile', {}).get('name', 'Unknown company')

        initial_cover = self.llm.prompt(message=f"""
            Create a cover letter for the {position} position at {company_name}.
            Job description: {job_description}
            Based on my resume: {resume}
            be sure the adjust the output of this cover letter to austrlian type language for example convert 'ize' type words such as optimize, customize, utilize, etc to optimise, customise, utilise, etc
            be sure to format this cover letter with dot points & line breaks to clearly outline sections/items as this text will be converted to a pdf file
            structure the cover letter as follows:
            Dear first name - last name extracted from {email}
            contents of the email
            Best Regards
            {YOUR_NAME}
            treat this as a final copy & only return the contents of the email
        """, new_conversation=True)

        cleaned_letter = re.sub(rf".*?(Dear .*?Best Regards\n{YOUR_NAME}\n).*", r"\1", initial_cover['message'], flags=re.DOTALL)
        return cleaned_letter

    def write_email_contents(self):
        email_content = self.llm.prompt(message=f"""
            Now write the contents of the email, I have scraped these email of these recruiters so keep the cold email brief and to the point, I will also be attaching my resume and cover letter
            format the email in as follows & exclude a subject:
            Dear first name
            contents of email
            Best Regards
            {YOUR_NAME}
        """)

        cleaned_email_content = re.sub(rf".*?(Dear .*?Best Regards\n{YOUR_NAME}\n).*", r"\1", email_content['message'], flags=re.DOTALL)
        return cleaned_email_content

class EmailSender:
    def __init__(self):
        self.sender_email = os.getenv("SENDER_MAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
    
    def send_application(self, 
                        recipient_email: str,
                        job_data: Dict,
                        email_body: str,
                        resume_path: str,
                        cover_letter_path: str) -> bool:
        """
        Send job application email with resume and cover letter attachments
        """
        try:
            msg = self._prepare_email(
                recipient_email=recipient_email,
                job_data=job_data,
                email_body=email_body,
                attachments=[
                    ('resume', resume_path),
                    ('cover_letter', cover_letter_path)
                ]
            )
            self._send_email(msg)
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def _prepare_email(self,
                      recipient_email: str,
                      job_data: Dict,
                      email_body: str,
                      attachments: List[Tuple[str, str]]) -> MIMEMultipart:
        """
        Prepare email message with body and attachments
        """
        position = job_data.get('title')
        
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Application for {position}"
        
        # Attach email body
        msg.attach(MIMEText(email_body, 'plain'))
        
        # Attach files
        for file_type, file_path in attachments:
            try:
                with open(file_path, 'rb') as file:
                    part = MIMEBase('application', 'pdf')
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    
                    # Set filename based on type
                    filename = os.path.basename(file_path)
                    if not filename.lower().endswith('.pdf'):
                        filename = f"{filename}.pdf"
                    
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{filename}"'
                    )
                    msg.attach(part)
            except Exception as e:
                print(f"Failed to attach {file_type}: {e}")
                raise
        
        return msg
    
    def _send_email(self, msg: MIMEMultipart):
        """
        Send email using SMTP
        """
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)

class ApplicationPipeline:
    def __init__(self, run_config: Dict, resume: str, applied_path: str="applied.csv"):
        self.scraper = JobScraper(run_config)
        self.email_sender = EmailSender()
        self.resume = resume
        self.applied_path = applied_path
        self.applied = self._load_applied_emails()
    
    def _load_applied_emails(self):
        if not os.path.exists(self.applied_path):
            open(self.applied_path, 'w').close()
            return []
        
        if os.path.getsize(self.applied_path) == 0:
            return []
        
        with open(self.applied_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)
            applied = [row for row in reader]
        
        return applied

    def _write_applied(self):
        with open(self.applied_path, 'w', newline='') as file:
            fieldnames = ['email', 'id']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.applied:
                writer.writerow({'email': row[0], 'id': row[1]})

    def run(self):
        """Execute the complete application pipeline"""
        # 1. Scrape job listings
        print("Scraping job listings...")
        job_data = self.scraper.scrape()

        # 2. Extract contact information
        print("Extracting contact information...")
        jobs = [
            job
            for job in job_data if job['contacts']
            for contact in job['contacts'] if contact['type'].lower() == 'email'
        ]
        
        print(f"Found {len(jobs)} jobs with contact information")
   
        # 3. Process each job and send applications
        for job in jobs:
            try:
                job_id = job['id']
                self.agent = AIAgent()
            
                # Skips job that don't have a wfh option and aren't in Sydney
                if "Hybrid" not in job['workArrangements'] and "Sydney" not in job['joblocationInfo']['location']:
                    continue

                # Skips jobs that don't have an email
                emails = [email['value'] for email in job['contacts'] if email['type'].lower() == "email"]
                if not emails:
                    continue
                
                applied_emails = [item[0] for item in self.applied]
                position = job.get('title', '')
                
                for email in emails:
                    if email in applied_emails:
                        continue
                    # Generate cover letter
                    cover_letter = self.agent.prepare_cover_letter(job, self.resume, email)
                    msg = self.agent.write_email_contents()

                    generate_cover_letter_pdf(cover_letter)

                    # Send application
                    success = self.email_sender.send_application(
                        email,
                        job,
                        msg,
                        "resume.pdf",
                        "coverletter.pdf"
                    )
                    if success:
                        print(f"Successfully processed application to {email} for {position}, {job_id}")
                        self.applied.append([email, job_id])
                    else:
                        print(f"Failed to send application to {email}, {job_id}")
                    # Wait 30sec to not overload api can be removed if using official apis
                    time.sleep(30)
                    
            except Exception as e:
                print(f"Error processing job application: {e}")
                time.sleep(30)
                continue

        self._write_applied()

def main():
    # Configuration
    searches = [
        "Junior Software Engineer"
        "Software Engineer",
        "Software Developer",
        "Junior Software Developer",
        "Entry Level Software Developer",
    ]

    resume_txt = "resume.txt"

    for search in searches:
        print(f"Performing search for {search}")
        run_config = {
            "searchTerm": search,
            "maxResults": 550,
            'SortBy': "ListedDate",
            'information-communication-technology': True
        }

        with open(resume_txt, 'r') as file:
            resume = file.read()
        # Initialize and run pipeline
        pipeline = ApplicationPipeline(run_config, resume)
        pipeline.run()

if __name__ == "__main__":
    main()
