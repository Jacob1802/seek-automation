from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def generate_cover_letter_pdf(cover_letter: str, output_file: str):
    # Create a PDF file
    document = SimpleDocTemplate(output_file, pagesize=A4)

    # Create styles for the document
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Body", fontSize=12, leading=15, spaceAfter=8))
    styles.add(ParagraphStyle(name="SectionHeader", fontSize=12, leading=14, spaceAfter=6, spaceBefore=12, fontName="Helvetica-Bold"))

    # Format the cover letter text
    formatted_lines = format_cover_letter(cover_letter)

    # Create the content elements
    content = []
    current_style = styles["Body"]
    for line in formatted_lines:
        if line.endswith(":"):
            current_style = styles["SectionHeader"]
        else:
            current_style = styles["Body"]
        content.append(Paragraph(line, current_style))
        if not line.strip():
            content.append(Spacer(1, 0.2 * inch))  # Add space for empty lines

    # Generate PDF
    document.build(content)
    logging.info(f"{output_file} has been created successfully.")

def format_cover_letter(cover_letter: str):
    lines = cover_letter.split("\n")
    formatted_lines = []
    for line in lines:
        if ":" in line:
            header, section = line.split(":", 1)
            header = header.strip() + ":"
            formatted_lines.append(header)
            formatted_lines.append(section.strip())
        else:
            if line.strip():
                formatted_lines.append(line.strip())
    return formatted_lines