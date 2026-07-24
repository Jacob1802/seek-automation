"""LLM call stubs for generating application text."""
import os

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def generate_cover_letter(context: dict) -> str:
    """Return a generated cover letter text given context dict (name, position, company, skills...).
    Replace this stub with the real API call (openai / your LLM client).
    """
    prompt = f"Create a concise German cover letter for {context.get('name')} applying to {context.get('position')} at {context.get('company')}. Include relevant skills: {context.get('skills')}."
    # TODO: call OpenAI or other LLM here and return the text
    return "[GENERATED COVER LETTER TEXT PLACEHOLDER]"