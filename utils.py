import os
import re
import html
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config


# Map app language codes to deep-translator language codes.
# Shared by blueprints/senior.py and blueprints/youth.py.
LANG_MAP = {
    'zh': 'zh-CN',
    'ms': 'ms',
    'ta': 'ta',
    'en': 'en',
}


def escape_html(text):
    """
    Escape HTML special characters to prevent XSS attacks.

    Args:
        text (str): The input text to escape.

    Returns:
        str: The HTML-escaped text.
    """
    if not text:
        return ""
    return html.escape(str(text), quote=True)


def sanitize_for_display(text):
    """
    Sanitize text for safe display: escape HTML and filter profanities.

    Args:
        text (str): The input text to sanitize.

    Returns:
        str: The sanitized text safe for HTML display.
    """
    if not text:
        return ""
    # First escape HTML to prevent XSS
    escaped = escape_html(text)
    # Then filter profanities
    return filter_text(escaped)


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


def check_unkind_words(content, unkind_words=None):
    """
    Check if content contains any unkind words.
    Uses two passes:
      1. Word-boundary regex  – catches normally spaced profanity.
      2. Stripped substring   – catches concatenated bypasses like NIGGANIGGA.
    Short words that appear inside legitimate English words (hell→hello,
    kill→skill, dick→Dickens) are kept boundary-only to avoid false positives.
    """
    if not content:
        return False

    if unkind_words is None:
        unkind_words = getattr(Config, 'UNKIND_WORDS', [])

    # Words that must use \b only (they appear inside innocent English words)
    boundary_only = {'hell', 'kill', 'dick', 'die'}

    content_lower = content.lower()
    # Strip everything that isn't a letter for the concatenation check
    content_stripped = re.sub(r'[^a-z]', '', content_lower)

    for word in unkind_words:
        word_lower = word.lower()

        # Pass 1: word-boundary match (catches spaced/standalone profanity)
        pattern = re.compile(r'\b' + re.escape(word_lower) + r'\b', re.IGNORECASE)
        if pattern.search(content):
            return True

        # Pass 2: stripped substring match (catches NIGGANIGGA-style bypasses)
        # Only for words not in boundary_only, and at least 3 chars long
        word_stripped = re.sub(r'[^a-z]', '', word_lower)
        if word_stripped not in boundary_only and len(word_stripped) >= 3:
            if word_stripped in content_stripped:
                return True

    return False


def save_uploaded_file(file, upload_folder, prefix='', allowed_extensions=None):
    """
    Handle file upload with unique naming and validation.

    Args:
        file: The file object from request.files.
        upload_folder (str): Directory path to save the file.
        prefix (str, optional): Prefix for the filename. Defaults to ''.
        allowed_extensions (set, optional): Allowed file extensions.
            Defaults to Config.ALLOWED_EXTENSIONS.

    Returns:
        str: The unique filename if successful, None if validation fails.
    """
    if not file or not file.filename:
        return None

    if allowed_extensions is None:
        allowed_extensions = getattr(Config, 'ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'bmp', 'mp4', 'mov', 'avi', 'webm', 'mkv'})

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    if ext not in allowed_extensions:
        return None

    # Ensure upload directory exists
    os.makedirs(upload_folder, exist_ok=True)

    # Create unique filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S_')
    unique_filename = f"{prefix}{timestamp}{filename}"

    # Save the file
    file.save(os.path.join(upload_folder, unique_filename))

    return unique_filename
