"""
Setup database schema using psycopg v3
"""
import psycopg

conn_string = "postgresql://admin:admin123@postgres:5432/newsdb"

def setup_schema():
    """Create tables for articles, users, and interactions"""
    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Create articles table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT,
                        category VARCHAR(100),
                        source VARCHAR(200),
                        published_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(source, title)
                    )
                """)
                
                # Create users table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        email VARCHAR(200) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create interactions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS interactions (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(100) NOT NULL,
                        article_id INTEGER NOT NULL REFERENCES articles(id),
                        interaction_type VARCHAR(50),
                        rating FLOAT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                print("✅ Database schema created successfully")
                
                # Check article count
                cur.execute("SELECT COUNT(*) FROM articles")
                count = cur.fetchone()[0]
                print(f"📊 Current articles: {count}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    setup_schema()
