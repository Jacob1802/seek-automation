from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from dotenv import load_dotenv
from email import encoders
from pathlib import Path
import logging
import imaplib
import smtplib
import email
import re
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class MailClient:
    def __init__(self, mail_protocol):
        self.user_email = os.getenv("EMAIL_ADDRESS")
        self.app_password = os.getenv("EMAIL_APP_PASSWORD")
        self.mail_protocol = mail_protocol
        self.smtp_port = 587
    
    def send_application(self, recipient_email, job_data, email_body, resume_path, cover_letter_path):
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
            logging.error(f"Failed to send email: {e}")
            return False
    
    def _prepare_email(self, recipient_email, job_data, email_body, attachments):
        position = job_data.get('title')
        
        msg = MIMEMultipart()
        msg['From'] = self.user_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Application for {position}"
        
        msg.attach(MIMEText(email_body, 'plain'))
        
        for file_type, file_path in attachments:
            try:
                part = MIMEBase('application', 'pdf')
                part.set_payload(Path(file_path).read_bytes())
                encoders.encode_base64(part)
                
                filename = os.path.basename(file_path)
                if not filename.lower().endswith('.pdf'):
                    filename = f"{filename}.pdf"
                
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{filename}"'
                )
                msg.attach(part)
            except Exception as e:
                logging.error(f"Failed to attach {file_type}: {e}")
                raise
        
        return msg
    
    def _send_email(self, msg):
        with smtplib.SMTP(self.mail_protocol, self.smtp_port) as server:
            server.starttls()
            server.login(self.user_email, self.app_password)
            server.send_message(msg)
    
    def parse_code(self, subject):
        match = re.search(r"\b\d{6}\b", subject)
        if not match:
            raise RuntimeError(f"Error parsing code from subject: '{subject}'")

        return match.group(0)

    def fetch_code(self, from_):
        msg = self.fetch_last_email(from_=from_)
        subject, encoding = decode_header(msg["Subject"])[0]

        if isinstance(subject, bytes):
            subject = subject.decode(encoding or 'utf-8')

        code = self.parse_code(subject)
        return code
    
    def fetch_last_email(self, from_):
        with imaplib.IMAP4_SSL(f"imap.{self.mail_protocol}") as mail:
            messages = self.fetch_emails(mail=mail, from_=from_)
            email_ids = messages[0].split()
            if not email_ids:
                print(f"No emails found from {from_} in the inbox.")
                return

            latest_email_id = email_ids[-1]
            status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            return msg
    
    def fetch_emails(self, mail, from_):
        try:
            mail.login(self.user_email, self.app_password)
            mail.select("inbox")
            status, messages = mail.search(None, 'FROM', from_)
        
            return messages
            
        except imaplib.IMAP4.error as e:
            print(f"\nIMAP Error: Could not retrieve email. Check your credentials and ensure IMAP is enabled.")
            print(f"Details: {e}")

if __name__ == '__main__':
    client = MailClient("gmail.com")
    print(client.fetch_code("noreply@seek.com.au"))