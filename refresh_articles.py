import psycopg
from datetime import datetime
from scraper import NewsAPIScraper

class ArticleDatabase:
    """Handle database operations for articles"""
    
    def __init__(self):
        self.conn_string = "postgresql://admin:admin123@postgres:5432/newsdb"
    
    def get_connection(self):
        """Get database connection"""
        return psycopg.connect(self.conn_string)
    
    def insert_articles(self, articles):
        """
        Insert articles into database
        
        Args:
            articles: List of article dictionaries
        
        Returns:
            Number of articles inserted
        """
        if not articles:
            return 0
        
        conn = self.get_connection()
        
        insert_query = """
        INSERT INTO articles (title, content, category, published_at, source)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (source, title) DO NOTHING
        """
        
        try:
            with conn.cursor() as cur:
                inserted_count = 0
                for article in articles:
                    cur.execute(insert_query, (
                        article.get('title', ''),
                        article.get('content', ''),
                        article.get('category', 'general'),
                        article.get('published_date'),
                        article.get('source', '')
                    ))
                    inserted_count += cur.rowcount
                
                conn.commit()
                print(f"✓ Inserted {inserted_count} articles")
                return inserted_count
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Error inserting articles: {e}")
            return 0
        finally:
            conn.close()
    
    def get_article_count(self):
        """Get total number of articles in database"""
        conn = self.get_connection()
        
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM articles")
            count = cur.fetchone()[0]
        
        conn.close()
        return count
    
    def get_category_counts(self):
        """Get article count by category"""
        conn = self.get_connection()
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT category, COUNT(*) as count
                FROM articles
                GROUP BY category
                ORDER BY count DESC
            """)
            results = cur.fetchall()
        
        conn.close()
        return results
    
    def get_latest_articles(self, limit=10):
        """Get latest articles from database"""
        conn = self.get_connection()
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, category, source, published_at
                FROM articles
                ORDER BY published_at DESC
                LIMIT %s
            """, (limit,))
            results = cur.fetchall()
        
        conn.close()
        return results

def refresh_articles(extract_full_content=False):
    """
    Main function to refresh articles in database
    
    Args:
        extract_full_content: Whether to extract full content (slower but more detailed)
    """
    print("=" * 70)
    print("News Article Refresh Script")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Initialize scraper and database
    scraper = NewsAPIScraper()
    db = ArticleDatabase()
    
    # Fetch articles from all categories
    print("Fetching articles from NewsAPI...")
    raw_articles = scraper.fetch_all_categories()
    
    if not raw_articles:
        print("✗ No articles fetched. Exiting.")
        return
    
    # Parse and clean articles
    print(f"\nParsing and cleaning {len(raw_articles)} articles...")
    parsed_articles = []
    
    for i, raw_article in enumerate(raw_articles, 1):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(raw_articles)} articles...")
        
        try:
            parsed = scraper.parse_article(raw_article, extract_full_content=extract_full_content)
            if parsed['title']:  # Only include articles with title
                parsed_articles.append(parsed)
        except Exception as e:
            print(f"✗ Error parsing article: {e}")
    
    print(f"✓ Successfully parsed {len(parsed_articles)} articles\n")
    
    # Insert into database
    print("Inserting articles into database...")
    inserted = db.insert_articles(parsed_articles)
    
    # Display statistics
    print("\n" + "=" * 70)
    print("Database Statistics")
    print("=" * 70)
    
    total_count = db.get_article_count()
    print(f"Total articles in database: {total_count}")
    
    print("\nArticles by category:")
    category_counts = db.get_category_counts()
    for category, count in category_counts:
        print(f"  {category}: {count}")
    
    print("\n" + "=" * 70)
    print("Latest Articles:")
    print("=" * 70)
    
    latest = db.get_latest_articles(5)
    for article in latest:
        article_id, title, category, source, pub_date = article
        title_short = title[:60] + "..." if len(title) > 60 else title
        print(f"[{category}] {title_short}")
        print(f"  Source: {source} | Published: {pub_date}")
        print()
    
    print("=" * 70)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

if __name__ == "__main__":
    # Run without full content extraction (faster)
    # Set extract_full_content=True to get full article content (slower)
    refresh_articles(extract_full_content=False)
