from application_pipeline.job_application_pipeline import ApplicationPipeline
from common.utils import load_json_file, extract_text_from_pdf
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
        assert Path(args.config_file).exists() == True, f"config not found in {args.config_file}"
    except AssertionError as e:
        logging.error(f"AssertionError: {e}")
        sys.exit(1)
    
    resume = extract_text_from_pdf(args.resume_pdf)
    run_config = load_json_file(args.config_file)

    for search in run_config["searchTerms"]:
        logging.info(f"Performing search for {search}")
        # Update search term on each iteration
        run_config["searchTerm"] = search
        pipeline = ApplicationPipeline(run_config, args.applied_path, args.smtp_protocol)
        pipeline.run(resume, args.resume_pdf, args.cover_letter_path, args.first_name, args.australian_language)

if __name__ == "__main__":
    main()
