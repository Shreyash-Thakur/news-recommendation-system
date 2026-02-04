import psycopg2
from config import DB_CONFIG

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to default postgres database (use 'newsdb' since it's already created by Docker)
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],  # Docker already created newsdb
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Database already exists from Docker, just confirm
        print(f"✓ Database '{DB_CONFIG['database']}' is ready")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        raise

def create_articles_table():
    """Create the articles table with proper schema"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create articles table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            category VARCHAR(50),
            published_date TIMESTAMP,
            source VARCHAR(255),
            url TEXT UNIQUE,
            author VARCHAR(255),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_category ON articles(category);
        CREATE INDEX IF NOT EXISTS idx_published_date ON articles(published_date);
        CREATE INDEX IF NOT EXISTS idx_source ON articles(source);
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        
        print("✓ Articles table created successfully with indexes")
        
        # Display table info
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'articles'
            ORDER BY ordinal_position;
        """)
        
        print("\nTable Schema:")
        print("-" * 60)
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")
        print("-" * 60)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        raise

def main():
    """Setup the complete database"""
    print("=" * 60)
    print("News Suggestion Database Setup")
    print("=" * 60)
    
    # Create database
    create_database()
    
    # Create articles table
    create_articles_table()
    
    print("\n✓ Database setup completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
