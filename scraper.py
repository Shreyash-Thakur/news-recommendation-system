import requests
from datetime import datetime
from newspaper import Article
from config import NEWS_API_KEY, NEWS_API_URL, CATEGORIES, COUNTRY, PAGE_SIZE
from text_cleaner import clean_article_data

class NewsAPIScraper:
    """Scraper for NewsAPI"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or NEWS_API_KEY
        self.base_url = NEWS_API_URL
        
        if not self.api_key:
            raise ValueError("NewsAPI key is required. Please set NEWS_API_KEY in .env file")
    
    def fetch_articles(self, category='general', country=COUNTRY, page_size=PAGE_SIZE):
        """
        Fetch articles from NewsAPI
        
        Args:
            category: News category (business, entertainment, general, health, science, sports, technology)
            country: Country code (e.g., 'us')
            page_size: Number of articles to fetch (max 100)
        
        Returns:
            List of article dictionaries
        """
        try:
            params = {
                'apiKey': self.api_key,
                'category': category,
                'country': country,
                'pageSize': min(page_size, 100)
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'ok':
                print(f"✗ API Error: {data.get('message', 'Unknown error')}")
                return []
            
            articles = data.get('articles', [])
            print(f"✓ Fetched {len(articles)} articles for category: {category}")
            
            return articles
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching articles: {e}")
            return []
    
    def fetch_all_categories(self):
        """Fetch articles from all categories"""
        all_articles = []
        
        for category in CATEGORIES:
            articles = self.fetch_articles(category=category)
            
            # Add category to each article
            for article in articles:
                article['category'] = category
            
            all_articles.extend(articles)
        
        print(f"\n✓ Total articles fetched: {len(all_articles)}")
        return all_articles
    
    def extract_full_content(self, url):
        """
        Extract full article content using newspaper3k
        
        Args:
            url: Article URL
        
        Returns:
            Full article text or None
        """
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            return article.text
        except Exception as e:
            print(f"✗ Error extracting content from {url}: {e}")
            return None
    
    def parse_article(self, raw_article, extract_full_content=False):
        """
        Parse raw article data into structured format
        
        Args:
            raw_article: Raw article data from NewsAPI
            extract_full_content: Whether to extract full content using newspaper3k
        
        Returns:
            Parsed and cleaned article dictionary
        """
        article = {
            'title': raw_article.get('title', ''),
            'description': raw_article.get('description', ''),
            'content': raw_article.get('content', ''),
            'category': raw_article.get('category', 'general'),
            'source': raw_article.get('source', {}).get('name', ''),
            'author': raw_article.get('author', ''),
            'url': raw_article.get('url', ''),
            'published_date': self._parse_date(raw_article.get('publishedAt'))
        }
        
        # Extract full content if requested
        if extract_full_content and article['url']:
            full_content = self.extract_full_content(article['url'])
            if full_content:
                article['content'] = full_content
        
        # Clean text data
        article = clean_article_data(article)
        
        return article
    
    def _parse_date(self, date_str):
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # NewsAPI returns ISO 8601 format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception as e:
            print(f"✗ Error parsing date {date_str}: {e}")
            return None

def test_scraper():
    """Test the scraper"""
    print("=" * 60)
    print("Testing NewsAPI Scraper")
    print("=" * 60)
    
    scraper = NewsAPIScraper()
    
    # Test fetching from one category
    articles = scraper.fetch_articles(category='technology', page_size=5)
    
    if articles:
        print("\n" + "=" * 60)
        print("Sample Article:")
        print("=" * 60)
        
        parsed = scraper.parse_article(articles[0])
        
        for key, value in parsed.items():
            if value:
                display_value = str(value)[:100] + "..." if len(str(value)) > 100 else value
                print(f"{key}: {display_value}")

if __name__ == "__main__":
    test_scraper()
