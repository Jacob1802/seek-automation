"""Orchestrator: load config, generate content, fill template, write output."""
import os
from pathlib import Path
from dotenv import load_dotenv
from src.generate_content import generate_cover_letter
from src.fill_template import fill_docx

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / 'output'

load_dotenv(ROOT / '.env')

def run_example():
    context = {
        'name': 'Max Mustermann',
        'position': 'Softwareentwickler',
        'company': 'Beispiel GmbH',
        'skills': 'Python, APIs, Testing'
    }
    text = generate_cover_letter(context)
    # The template should contain a placeholder like {{ cover_text }} or map fields individually
    tpl_context = {**context, 'cover_text': text}
    out_file = OUTPUT_DIR / f"anschreiben_{context['name'].replace(' ', '_')}.docx"
    fill_docx('anschreiben_template.docx', tpl_context, str(out_file))
    print(f"Wrote: {out_file}")

if __name__ == '__main__':
    run_example()