
from meta_ai_api import MetaAI
import re

class AIAgent:
    def __init__(self, your_name):
        self.llm = MetaAI()
        self.your_name = your_name
    
    def prepare_cover_letter(self, job_data, resume, email, convert_to_australian_language):
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
            Dear first name - last name extracted from {email}
            contents of the email
            Best Regards
            {self.your_name}
            treat this as a final copy & only return the contents of the email
            """
        
        initial_cover = self.llm.prompt(message=prompt, new_conversation=True)

        cleaned_letter = re.sub(rf".*?(Dear .*?Best Regards\n{self.your_name}\n).*", r"\1", initial_cover['message'], flags=re.DOTALL)
        return cleaned_letter

    def write_email_contents(self):
        email_content = self.llm.prompt(message=f"""
            Now write the contents of the email, I have scraped these email of these recruiters so keep the cold email brief and to the point, I will also be attaching my resume and cover letter
            format the email in as follows & exclude a subject:
            Dear first name
            contents of email
            Best Regards
            {self.your_name}
        """)

        cleaned_email_content = re.sub(rf".*?(Dear .*?Best Regards\n{self.your_name}\n).*", r"\1", email_content['message'], flags=re.DOTALL)
        return cleaned_email_content