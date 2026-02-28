import re

def clean_text(raw_text):
    try:
        # Remove unwanted characters and normalize whitespace
        cleaned_text = re.sub(r'[^\x00-\x7F]+', ' ', raw_text)  # Remove non-ASCII characters
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()  # Normalize whitespace
        return cleaned_text
    except Exception as e:
        raise RuntimeError(f"Text cleaning failed: {e}")