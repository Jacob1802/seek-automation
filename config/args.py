import argparse

parser = argparse.ArgumentParser()

def add_args():
    parser.add_argument('--first_name', 
                        type=str, 
                        help='Name of the user',
                        required=True)
    
    parser.add_argument('--resume_txt', 
                        type=str,
                        help='Path to resume.txt file',
                        default="application_materials/resume.txt")

    parser.add_argument('--resume_pdf', 
                        type=str,
                        help='Path to resume.pdf file',
                        default="application_materials/resume.pdf")

    parser.add_argument('--config_file', 
                        type=str,
                        help='Path to config file',
                        default="config/run_config.json")
    
    parser.add_argument('--cover_letter_path', 
                        type=str,
                        help='Path to save cover letter too',
                        default="application_materials/cover_letter.pdf")
    
    parser.add_argument('--applied_path', 
                        type=str,
                        help='Path to save applied jobs to',
                        default="application_materials/applied.csv")

    parser.add_argument('--smtp_protocol', 
                        type=str,
                        help='Protocol to send mail',
                        default="smtp.gmail.com")

    # This is set to True by default as seeks largest english userbase is Australia & NZ
    parser.add_argument('--australian_language', 
                        type=bool,
                        help='Convert llm output to australian type language',
                        default=True)

    return parser.parse_args()
