"""docxtpl helper to fill a .docx template with context data."""
from docxtpl import DocxTemplate
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / 'templates'

def fill_docx(template_name: str, context: dict, out_path: str) -> str:
    """Fill template and save to out_path. Returns saved file path."""
    tpl_path = TEMPLATES_DIR / template_name
    doc = DocxTemplate(str(tpl_path))
    doc.render(context)
    doc.save(out_path)
    return out_path