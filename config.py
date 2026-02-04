import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# NewsAPI Configuration
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
NEWS_API_URL = 'https://newsapi.org/v2/top-headlines'

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'news_suggestion'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

# Scraping Configuration
CATEGORIES = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']
COUNTRY = 'us'
PAGE_SIZE = 100
