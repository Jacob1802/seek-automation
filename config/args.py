import argparse

parser = argparse.ArgumentParser()

def add_args():
    parser.add_argument('--first_name', 
                        type=str, 
                        help='Name of the user',
                        required=True)

    parser.add_argument('--resume_pdf_path', 
                        type=str,
                        help='Path to resume',
                        default="application_pipeline/application_materials/resume.pdf")

    parser.add_argument('--config_path', 
                        type=str,
                        help='Path to config file',
                        default="config/run_config.json")
    
    parser.add_argument('--cover_letter_path', 
                        type=str,
                        help='Path to cover letter',
                        default="application_pipeline/application_materials/cover_letter.pdf")
    
    parser.add_argument('--applied_path', 
                        type=str,
                        help='Path to applied jobs',
                        default="application_pipeline/application_materials/applied.json")

    parser.add_argument('--mail_protocol', 
                        type=str,
                        help='Mail protocol e.g gmail.com, outlook.com',
                        default="gmail.com")

    # True by default as seeks largest english userbase is Australia & NZ
    parser.add_argument('--australian_language', 
                        type=int,
                        help='Convert llm output to australian type language. 0 = False',
                        default=1)

    parser.add_argument('--model', 
                        type=str,
                        help='openai gpt model',
                        default="gpt-4o-mini")

    parser.add_argument('--min_score', 
                        type=float,
                        help='Min job matching score',
                        default=0.4)
    
    parser.add_argument('--show_recent_role',
                            type=int,
                            help='Adds recent role to seek job application for employers. 0 = False',
                            default=1)
    
    args = parser.parse_args()
    args.australian_language = bool(args.australian_language)
    args.show_recent_role = bool(args.show_recent_role)

    return args
