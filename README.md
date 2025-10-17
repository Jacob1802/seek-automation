# Automated Seek Job Search

This project automates the process of applying for jobs by scraping job listings, generating customised cover letters and emails, and sending applications with attachments such as resumes and cover letters.

## Features

- **Job Scraping**: Uses the Apify Seek Job Scraper to fetch job listings based on search terms.
- **AI-Generated Cover Letters**: Customises cover letters using LLM (MetaAI), ensuring proper Australian formatting.
- **Automated Applications via Seek**: Automated login via email code & application to jobs directly on Seek.
- **Email Automation**: Sends job applications with attached resumes and cover letters to recruiters via Gmail.
- **Resume-Based Job Filtering**: Evaluates job listings against your resume content using a semantic similarity model. Only applies to jobs above a configurable similarity threshold, ensuring relevance and quality.
- **Tracking Applications**: Tracks sent applications to prevent duplicate submissions.

## Setup Requirements

1. **Apify API Key**  
   - Create an [Apify account](https://console.apify.com/) and obtain an [API key](https://console.apify.com/settings/integrations) for the Seek Job Scraper.
   - Store the API key in an `.env` file as `APIFY_KEY`.

2. **Mail App Password**  
   - Generate an App Password in your mail Account settings for your mail account.
   - Store the mail account & app password in the `.env` file as `EMAIL_ADDRESS` & `EMAIL_APP_PASSWORD`.

3. **Resume Preparation**  
   - Create the following files:
     - `application_pipeline/application_materials/resume.pdf`: A PDF version of your resume, attached to job applications.

4. **Apify API Key** (optional)
   - Create an [OpenAI account](https://platform.openai.com/) and obtain an [API key](https://platform.openai.com/settings/organization/api-keys).
   - Store the API key in an `.env` file as `OPENAI_KEY`.

## How to Use

1. **Clone the repository**:  
   ```bash
   git clone <repository-url>
   cd <repository>
   ```
2. **Copy .env.example to .env & edit .env**:
    ```bash
    APIFY_KEY=<Your Apify API Key>
    OPENAI_KEY=<Your Openai API Key>
    EMAIL_ADDRESS=<Your Mail Address>
    EMAIL_APP_PASSWORD=<Your Mail App Password>
    ```
4. **Prepare your resume files**:
    - Ensure `resume.pdf` exist in the `application_pipeline/application_materials` directory.
5. **Install uv**
    ```bash
    pip install uv
    ```
6. **Run the application**:
   ```bash
    uv run main.py
   ```

## Customisation
**Edit config/run_config.json to customise searches**:
 - `searchTerms`: Job titles to search
 - `maxResults`: Maximum number of job listings
 - `SortBy`: Sorting method for job listings options: ['ListedDate', 'KeywordRelevance']
 - `suburbOrCity`: Sydney
 - `state`: NSW
 - `dateRange`: Day range of jobs to collect 
 - `requireEmail`: Set to true if you only want to apply via email

**Advanced Configuration**:
 - For more detailed configuration options, refer to the Apify Seek Job Scraper documentation [actor documentation](https://apify.com/websift/seek-job-scraper).
 - For custom logic beyond the actor's capabilities, modify the `run()` method in `application_pipeline/job_application_pipeline.py`.

## Optional Arguments
 - `--resume_pdf`: Custom resume PDF path
 - `--config_file`: Custom config file path
 - `--cover_letter_path`: Custom cover letter save location
 - `--mail_protocol`: Mail server used e.g `gmail.com` or `outlook.com`.
- `--australian_language`: When turned on, it automatically uses Australian spelling (for example, “organise” instead of “organize”). This is on by default. 
 - `--model`: The openai model you wish to use for writing cover letters or emails.
- `--min_score`: Sets the minimum match score between your resume and a job description. Higher scores mean the system will only apply for jobs that are a closer fit to your experience.

## Notes
 - Currently only supports seek login via email code
 - Ensure your mail account has secure app access enabled or app-specific passwords configured.
 - Applications are tracked in `application_pipeline/application_materials/applied.json` to avoid sending duplicates.
 - Using other llms official APIs such as Openai or Claude would likely improve performance such as speed & higher quality responses.