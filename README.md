# Automated Seek Job Search

This project automates the process of applying for jobs by scraping job listings, generating customised cover letters and emails, and sending applications with attachments such as resumes and cover letters.

## Features

- **Job Scraping**: Uses the Apify Seek Job Scraper to fetch job listings based on search terms.
- **AI-Generated Cover Letters**: Customises cover letters using LLM (MetaAI), ensuring proper Australian formatting.
- **Email Automation**: Sends job applications with attached resumes and cover letters to recruiters via Gmail.
- **Tracking Applications**: Tracks sent applications to prevent duplicate submissions.

## Setup Requirements

1. **Apify API Key**  
   - Create an Apify account and obtain an API key for the Seek Job Scraper.
   - Store the API key in an `.env` file as `APIFY_KEY`.

2. **Mail App Password**  
   - Generate an App Password in your mail Account settings for your mail account.
   - Store the mail account & app password in the `.env` file as `SENDER_MAIL` & `SENDER_PASSWORD`.

3. **Resume Preparation**  
   - Create the following files:
     - `application_materials/resume.txt`: A plain-text version of your resume, used for AI-generated content.
     - `application_materials/resume.pdf`: A PDF version of your resume, attached to job applications.

## How to Use

1. **Clone the repository**:  
   ```bash
   git clone <repository-url>
   cd <repository>
   ```
2. **Create a virtual environment & install dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Copy .env.example to .env**:
    ```bash
    APIFY_KEY=<Your Apify API Key>
    SENDER_MAIL=<Your Mail Address>
    SENDER_PASSWORD=<Your Mail App Password>
    ```
4. **Prepare your resume files**:
    - Ensure `resume.txt` and `resume.pdf` exist in the `application_materials` directory.
5.
    **Run the application**:
    ```bash
    python3 apply.py --name [Your first name]
    ```

## Customisation
**Edit config/run_config.json to customise searches**:
 - `searchTerms`: Job titles to search
 - `maxResults`: Maximum number of job listings
 - `SortBy`: Sorting method for job listings options: ['ListedDate', 'KeywordRelevance']

**Advanced Configuration**:
 - For more detailed configuration options, refer to the Apify Seek Job Scraper documentation [actor documentation](https://apify.com/websift/seek-job-scraper).
 - For custom logic beyond the actor's capabilities, modify the `run()` method in `application_pipeline/job_application_pipeline.py`.

## Optional Arguments
 - `--resume_txt:` Custom resume text path
 - `--resume_pdf`: Custom resume PDF path
 - `--config_file`: Custom config file path
 - `--cover_letter_path`: Custom cover letter save location
 - `--smtp_protocol`: Custom SMTP server
 - `--australian_language`: Toggle Australian English e.g prompt llm to convert ize words to ise (default: True)

## Notes
- Ensure your mail account has secure app access enabled or app-specific passwords configured.
- Applications are tracked in `applied.csv` to avoid sending duplicates.