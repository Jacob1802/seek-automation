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
        company_name = company_profile.get('name', 'N/A')
        
        position = job_data.get('title', 'Unknown position')
        if company_name == 'N/A':
            company_name = 'Hiring Manager'

        australian_language = (
            "Adjust spelling to Australian English (e.g., optimise, customise, utilise instead of optimize, customize, utilize)."
            if convert_to_australian_language else ""
        )

        prompt = f"""
            ## Optimized Prompt for Generating a Cover Letter

            ### Goal
            You are an expert career consultant and professional writer. Your task is to generate a 
            **highly targeted, compelling, and professional cover letter** based on the provided 
            **Resume** and **Job Description** below.

            ### Required Inputs (Context)
            1.  **[RESUME_TEXT]:**
                ---
                {resume}
                ---
            2.  **[JOB_DESCRIPTION_TEXT]:**
                ---
                {job_description}
                ---* 
            3. **Company to Address:** {company_name}
            4. **Position Applied For:** {position}
            5.  **Format and Content Constraint (CRITICAL):**
                * Your output **MUST NOT** contain *any* generic placeholders enclosed in square brackets 
                (e.g., `[Company Name]`, `[Position Title]`).
                * **DO NOT** generate any content *before* the salutation or *after* the closing.
    
                * **Specifically, you MUST NOT include:**
                    - The current date
                    - A sender's address, postcode, or contact information (this is on the resume)
                    - A recipient's address or postcode
    
                * The output must start *directly* with the salutation (e.g., "Dear Hiring Manager,").
                * The output must end *directly* with the closing (e.g., "Sincerely,"). **Do not add a name after the closing.**
            ---

            ### Constraints and Negative Prompting

            The generated cover letter **must strictly adhere** to the following rules:

            1.  **Skills Fabrication Constraint (CRITICAL):**
                * **NEVER** invent, fabricate, or include any skill, technology, experience, 
                accomplishment, or responsibility in the cover letter that is **not explicitly 
                mentioned** in the provided **[resume]**.
            2.  **Length and Structure Constraint:** The cover letter must be **no more than 400 words** and must follow a standard professional three-to-five-paragraph business letter format.
            3.  **Tone Constraint:** The tone must be professional, confident, and enthusiastic.
            4.  **Language Constraint:** {australian_language}

            ---

            ### Generation Step

            Follow this **two-step process** for your final output:

            #### **Step 1: Analysis and Skill Mapping (Internal Step)**
            Internally, create a list of 5-7 **key required skills** from the **[JOB_DESCRIPTION_TEXT]**. 
            Then, cross-reference this list with the **[RESUME_TEXT]** to identify 3-5 **matching skills** that can be used as evidence in the letter.

            #### **Step 2: Cover Letter Generation (Primary Output)**
            Generate the complete cover letter using all the context and adhering to all constraints.

            ---

            ### **FINAL RESPONSE FORMAT**

            The final output must strictly follow this structure:

            ```
            [The complete, generated cover letter text, with no extra sections or commentary]
            ```
            """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a highly skilled, professional career writer. "
                        "Your sole task is to generate the complete cover letter text. "
                        "Respond *only* with the final, polished cover letter text. "
                        "Do not include any introductory remarks, commentary, explanations, "
                        "or any text other than the cover letter itself. "
                        "Adhere strictly to the requested structure and formatting rules."
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )

        cover_text = response.choices[0].message.content.strip()
        print(cover_text)
        print("-"*50)
        final_coverletter = self.review_coverletter(cover_text, resume, job_description)
        print(final_coverletter)
        print(cover_text == final_coverletter)
        return final_coverletter.strip('```')

    def review_coverletter(self, cover_letter_text, original_resume, original_job_description, adjustment_requests=""):
        prompt = f"""
            ## Optimized Prompt for Cover Letter Verification and Small Adjustments

            ### Goal
            You are an expert editor and compliance officer. Your task is to **verify** the provided cover 
            letter text against the original constraints and then apply any requested **small, stylistic 
            adjustments** without changing the core factual evidence.

            ### Required Inputs (Context)
            1.  **[COVER_LETTER_TEXT]:** (The letter to be edited)
                ---
                {cover_letter_text}
                ---
            2.  **[ORIGINAL_RESUME_TEXT]:** (Used for re-verification)
                ---
                {original_resume}
                ---
            3.  **[ORIGINAL_JOB_DESCRIPTION_TEXT]:** (Used for context)
                ---
                {original_job_description}
                ---
            4.  **[ADJUSTMENT_REQUESTS]:**
                ---
                {adjustment_requests or "No specific adjustments provided. Focus only on verification and minor flow improvements."}
                ---

            ### Verification Constraints (CRITICAL)

            You **MUST** ensure the following rules are still strictly met in the final output:

            1.  **NO SKILLS FABRICATION:** The letter *cannot* contain any skill, experience, or claim that is not factually supported by the **[ORIGINAL_RESUME_TEXT]**.
            2.  **LENGTH/STRUCTURE:** The main cover letter body must remain **under 500 words** and follow a professional business letter structure.
            ---

            ### Adjustment Process
            
            1.  **Verification:** First, internally re-verify the **[COVER_LETTER_TEXT]** against the factual content of the **[ORIGINAL_RESUME_TEXT]**. If a factual error is found (a fabricated skill), **correct the error** by removing the fabricated statement.
            2.  **Refinement:** Apply any changes requested in the **[ADJUSTMENT_REQUESTS]** while respecting all constraints. If no specific requests are made, make only very minor, high-quality, flow-of-text improvements.
            3. **PLACEHOLDER REMOVAL (MANDATORY RULE):**
                - Your final output **MUST NOT** contain any square brackets (`[` or `]`).
                - If you find *any* text enclosed in square brackets (e.g., `[Date]`, `[Your Address]`, `[Company Name]`), 
                  you **must delete the placeholder text AND the brackets entirely.**
                - **Example Transformation:**
                    - ❌ **Input:** `[Date] \n [Your Address] \n [Postcode] \n \n Dear [Hiring Manager], \n I am applying for the role...`
                    - ✅ **Correct Output:** `\n \n Dear , \n I am applying for the role...`
            4.  **Final Output:** Produce the final, polished cover letter text.
            ---

            ### **FINAL RESPONSE FORMAT**

            Your final output must be **ONLY** the completely verified and adjusted cover letter. Do not include any commentary, analysis, or introductory text.

            ```
            [The complete, verified, and adjusted cover letter text]
            ```
            """
        
        response = self.client.chat.completions.create(
        model=self.model,
        messages=[
                {
                    "role": "system",
                    "content": (
                    "You are a professional editor and compliance specialist. "
                        "Your sole task is to verify and adjust the provided cover letter text. "
                        "Your response must ONLY be the final, verified, and adjusted cover letter. "
                        "Strictly adhere to all constraints, especially the 'NO SKILLS FABRICATION' rule."
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )

        final_coverletter = response.choices[0].message.content.strip().replace('-', '')
        return final_coverletter

    def write_email_contents(self):
        email_prompt = f"""
            **Task:** Write a short, polite cold email to a recruiter.
            The email must mention that the resume and cover letter are attached.
            Do not include a subject line.

            **Required Output Format (Strictly follow this):**
            Dear Hiring Manager,
            [contents of email]
            Best Regards
            {self.name}
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant specialized in drafting concise, professional, "
                        "and polite cold emails for recruiters. Your *only* output must be the "
                        "email body text. Do not include a subject line, any introductory or "
                        "concluding commentary, or extra text of any kind. Strict adherence to "
                        "the provided email format is required."
                    )
                },
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
