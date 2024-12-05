from application_pipeline.job_application_pipeline import ApplicationPipeline
from config.args import add_args
from pathlib import Path
import logging
import json
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def main():
    args = add_args()
    try:
        assert Path(args.resume_pdf).exists() == True, f"resume.pdf not found in {args.resume_pdf}"
        assert Path(args.resume_txt).exists() == True, f"resume.txt not found in {args.resume_txt}"
        assert Path(args.config_file).exists() == True, f"config not found in {args.config_file}"
    except AssertionError as e:
        logging.error(f"AssertionError: {e}")
        sys.exit(1)
    
    try:
        resume = Path(args.resume_txt).read_text()
        run_config = json.loads(Path(args.config_file).read_bytes())
    except Exception as e:
        logging.error(e)
        sys.exit(1)

    for search in run_config["searchTerms"]:
        logging.info(f"Performing search for {search}")
        # Update search term on each iteration
        run_config["searchTerm"] = search
        pipeline = ApplicationPipeline(run_config, args.applied_path, args.smtp_protocol)
        pipeline.run(resume, args.resume_pdf, args.cover_letter_path, args.first_name, args.australian_language)

if __name__ == "__main__":
    main()
