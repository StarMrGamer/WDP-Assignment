import re
from config import Config

def filter_text(text):
    """
    Filters profanities and unkind words from the given text.
    Replaces found words with asterisks matching the word length.
    
    Args:
        text (str): The input text to filter.
        
    Returns:
        str: The filtered text.
    """
    if not text:
        return ""
        
    filtered_text = text
    # Get words from config, default to empty list if not found
    unkind_words = getattr(Config, 'UNKIND_WORDS', [])
    
    for word in unkind_words:
        # Use regex to replace whole words only, case-insensitive
        # \b ensures we match "word" but not "sword"
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        filtered_text = pattern.sub('*' * len(word), filtered_text)
        
    return filtered_text
