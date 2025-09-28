from application_pipeline.job_application_pipeline import ApplicationPipeline
from common.utils import load_json_file, extract_text_from_pdf
from config.args import add_args
from dotenv import load_dotenv
from pathlib import Path
import logging
import asyncio
import sys
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

async def main():
    args = add_args()
    try:
        assert Path(args.resume_pdf_path).exists() == True, f"resume.pdf not found in {args.resume_pdf_path}"
        assert Path(args.config_path).exists() == True, f"config not found in {args.config_path}"
    except AssertionError as e:
        logging.error(f"AssertionError: {e}")
        sys.exit(1)
    
    resume_txt = extract_text_from_pdf(args.resume_pdf_path)
    run_config = load_json_file(args.config_path)

    args.resume_txt = resume_txt
    if os.getenv("OPENAI_KEY"):
        args.use_openai = True
    else:
        args.use_openai = False
        logging.warning("No openai api found defaulting to meta api")

    pipeline = ApplicationPipeline(run_config, args)
    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main())
