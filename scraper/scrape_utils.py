import hashlib
import re
from bs4 import BeautifulSoup

# Helper functions
def clean_text(text):
    """Cleans and normalizes a text by stripping extra spaces."""
    return ' '.join(text.split()).strip() if text else 'N/A'

def clean_list(text):
    """Converts a block of text into a list of bullet points."""
    if not text:
        return 'N/A'
    # Handle abbreviations with periods correctly
    text = re.sub(r'\b(?:e\.g|i\.e|etc|Dr|Mr|Mrs|Ms|Jr|Sr|vs|Inc|Ltd|Co|Prof|PhD|M\.D|B\.Sc)\.', 
                  lambda m: m.group(0).replace('.', '[DOT]'), text)
    # Create bullet points for each sentence
    return '\n'.join(f"- {sentence.strip()}." for sentence in text.split('.') if sentence.strip()).replace('[DOT]', '.')

# Function to generate a unique ID if reference_number doesn't exist
def generate_unique_id(job_posting):
    """Generates a unique identifier for a job posting."""
    identifier_str = f"{job_posting.title}_{job_posting.employer_name}_{job_posting.location}"
    return hashlib.sha256(identifier_str.encode('utf-8')).hexdigest()
