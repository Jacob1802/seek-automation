from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from email import encoders
import smtplib
import os

load_dotenv()

class EmailSender:
    def __init__(self, smtp_protocol):
        self.sender_email = os.getenv("SENDER_MAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.smtp_server = smtp_protocol
        self.smtp_port = 587
    
    def send_application(self, 
                        recipient_email: str,
                        job_data: Dict,
                        email_body: str,
                        resume_path: str,
                        cover_letter_path: str) -> bool:
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
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)