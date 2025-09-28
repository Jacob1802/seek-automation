from meta_ai_api import MetaAI
from dotenv import load_dotenv
from openai import OpenAI
import logging
import os
import re

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class AIAgent:
    def __init__(self, name, model=""):
        if os.getenv("OPENAI_KEY"):
            self.agent = OpenAiAgent(name, model)
        else:
            self.agent = MetaAI(name)


class OpenAiAgent:
    def __init__(self, name, model):
        self.client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
        self.model = model
        self.name = name
    
    def prepare_cover_letter(self, job_data, resume, convert_to_australian_language):
        job_content = job_data.get('content', {})
        job_description = job_content.get('sections', '')
        
        company_profile = job_data.get('companyProfile', {})
        company_name = company_profile.get('name', 'Unknown company')
        
        position = job_data.get('title', 'Unknown position')

        australian_language = (
            "Adjust spelling to Australian English (e.g., optimise, customise, utilise instead of optimize, customize, utilize)."
            if convert_to_australian_language else ""
        )

        prompt = f"""
            **Task:** Create a professional and compelling cover letter for the **{position}** position at **{company_name}**.

            **Contextual Data:**
            - Job Description: {job_description}
            - My Resume/Experience: {resume}

            **Formatting and Output Requirements:**
            1. The letter must be formatted with **dot points** (bullet points) and clear **line breaks** to ensure readability when converted to PDF.
            2. The letter must directly address the requirements and skills mentioned in the Job Description, backed up by evidence from the Resume/Experience.
            3. {australian_language}

            **Required Final Structure (Strictly follow this):**
            Dear {company_name}
            [Contents of the letter body]
            Best Regards
            {self.name}
        """

        initial_cover = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "You are a highly skilled, professional career writer. Your sole task is to generate the complete cover letter text. Respond *only* with the final, polished cover letter text. Do not include any introductory remarks, commentary, explanations, or any text other than the cover letter itself. Adhere strictly to the requested structure and formatting rules."},
                {"role": "user", "content": prompt}
            ]
        )

        cover_text = initial_cover.choices[0].message.content.strip()
        return cover_text

    def write_email_contents(self):
        email_prompt = f"""
            **Task:** Write a short, polite cold email to a recruiter.
            The email must mention that the resume and cover letter are attached.
            Do not include a subject line.

            **Required Output Format (Strictly follow this):**
            Dear [first name]
            [contents of email]
            Best Regards
            {self.name}
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "You are an AI assistant specialized in drafting concise, professional, and polite cold emails for recruiters. Your *only* output must be the email body text. Do not include a subject line, any introductory or concluding commentary, or extra text of any kind. Strict adherence to the provided email format is required."},
                {"role": "user", "content": email_prompt}
            ]
        )

        email_text = response.choices[0].message.content.strip()
        return email_text


class MetaAgent:
    def __init__(self, name):
        self.client = MetaAI()
        self.name = name
    
    def prepare_cover_letter(self, job_data, resume, convert_to_australian_language):
        job_description = job_data.get('content', '').get('sections', '')
        position = job_data.get('title', 'Unknown position')
        company_name = job_data.get('companyProfile', {}).get('name', 'Unknown company')

        australian_language = "be sure the adjust the output of this cover letter to austrlian type language for example convert 'ize' type words such as optimize, customize, utilize, etc to optimise, customise, utilise, etc"


        prompt = f"""
            Create a cover letter for the {position} position at {company_name}.
            Job description: {job_description}
            Based on my resume: {resume}
            {australian_language if convert_to_australian_language else ""}
            be sure to format this cover letter with dot points & line breaks to clearly outline sections/items as this text will be converted to a pdf file
            structure the cover letter as follows:
            Dear {company_name}
            contents of the email
            Best Regards
            {self.name}
            treat this as a final copy & only return the contents of the email
            """
        
        initial_cover = self.client.prompt(message=prompt, new_conversation=True)

        cleaned_letter = re.sub(rf".*?(Dear .*?Best Regards\n{self.name}\n).*", r"\1", initial_cover['message'], flags=re.DOTALL)
        return cleaned_letter

    def write_email_contents(self):
        email_content = self.client.prompt(message=f"""
            Now write the contents of the email, I have scraped these email of these recruiters so keep the cold email brief and to the point, I will also be attaching my resume and cover letter
            format the email in as follows & exclude a subject:
            Dear first name
            contents of email
            Best Regards
            {self.name}
        """)

        cleaned_email_content = re.sub(rf".*?(Dear .*?Best Regards\n{self.name}\n).*", r"\1", email_content['message'], flags=re.DOTALL)
        return cleaned_email_content
