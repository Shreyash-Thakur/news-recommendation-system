"""
Simple NewsAPI article fetcher without newspaper3k dependency
"""
import psycopg
import requests
from datetime import datetime

API_KEY = "359da6bdb43d4950b34b8ef6612f6559"
conn_string = "postgresql://admin:admin123@postgres:5432/newsdb"

categories = ['technology', 'business', 'science', 'health', 'sports', 'entertainment', 'general']

print("🔄 Fetching articles from NewsAPI...")

total_inserted = 0

for category in categories:
    url = f"https://newsapi.org/v2/top-headlines?category={category}&language=en&pageSize=50&apiKey={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('status') != 'ok':
            print(f"⚠️  {category}: {data.get('message', 'Unknown error')}")
            continue
        
        articles = data.get('articles', [])
        
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                inserted = 0
                for article in articles:
                    title = article.get('title', '').strip()
                    description = article.get('description', '')
                    content = article.get('content', '')
                    source = article.get('source', {}).get('name', 'Unknown')
                    published_at = article.get('publishedAt')
                    
                    if not title or title == '[Removed]':
                        continue
                    
                    # Combine description and content
                    full_content = f"{description} {content}".strip() if description or content else None
                    
                    try:
                        cur.execute("""
                            INSERT INTO articles (title, content, category, source, published_at)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (source, title) DO NOTHING
                        """, (title, full_content, category, source, published_at))
                        inserted += 1
                    except Exception as e:
                        pass
                
                conn.commit()
                print(f"✅ {category}: {inserted} articles")
                total_inserted += inserted
                
    except Exception as e:
        print(f"❌ {category}: {e}")

print(f"\n📊 Total articles inserted: {total_inserted}")

# Show final count
with psycopg.connect(conn_string) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM articles")
        total = cur.fetchone()[0]
        print(f"📊 Total articles in database: {total}")
