import re
from bs4 import BeautifulSoup
from html import unescape

def remove_html_tags(text):
    """Remove HTML tags from text using BeautifulSoup"""
    if not text:
        return ""
    
    # Parse HTML
    soup = BeautifulSoup(text, 'lxml')
    
    # Extract text
    text = soup.get_text()
    
    # Unescape HTML entities
    text = unescape(text)
    
    return text

def normalize_whitespace(text):
    """Normalize whitespace in text"""
    if not text:
        return ""
    
    # Replace multiple whitespaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Replace multiple newlines with single newline
    text = re.sub(r'\n+', '\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def remove_special_characters(text, keep_punctuation=True):
    """Remove special characters while optionally keeping punctuation"""
    if not text:
        return ""
    
    if keep_punctuation:
        # Keep letters, numbers, spaces, and basic punctuation
        text = re.sub(r'[^a-zA-Z0-9\s\.\,\!\?\-\:\;\'\"]', '', text)
    else:
        # Keep only letters, numbers, and spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    
    return text

def clean_text(text, remove_html=True, normalize_ws=True, remove_special=False):
    """
    Complete text cleaning pipeline
    
    Args:
        text: Text to clean
        remove_html: Remove HTML tags
        normalize_ws: Normalize whitespace
        remove_special: Remove special characters
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove HTML tags
    if remove_html:
        text = remove_html_tags(text)
    
    # Remove special characters
    if remove_special:
        text = remove_special_characters(text)
    
    # Normalize whitespace
    if normalize_ws:
        text = normalize_whitespace(text)
    
    return text

def clean_article_data(article):
    """
    Clean all text fields in an article dictionary
    
    Args:
        article: Dictionary with article data
    
    Returns:
        Cleaned article dictionary
    """
    cleaned = article.copy()
    
    # Fields to clean
    text_fields = ['title', 'description', 'content']
    
    for field in text_fields:
        if field in cleaned and cleaned[field]:
            cleaned[field] = clean_text(cleaned[field])
    
    return cleaned

if __name__ == "__main__":
    # Test the cleaning functions
    test_html = """
        <div class="article">
            <h1>Test Article</h1>
            <p>This is a test   with    multiple   spaces.</p>
            <p>And &nbsp; some &amp; HTML entities.</p>
        </div>
    """
    
    print("Original:")
    print(test_html)
    print("\nCleaned:")
    print(clean_text(test_html))
