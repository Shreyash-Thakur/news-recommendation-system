"""
Add embedding column to articles table for storing precomputed embeddings.
Run this ONCE before generating embeddings.
"""

import psycopg

# Database connection
conn_string = "postgresql://admin:admin123@postgres:5432/newsdb"

try:
    with psycopg.connect(conn_string) as conn:
        with conn.cursor() as cur:
            # Add embedding column if it doesn't exist
            cur.execute("""
                ALTER TABLE articles 
                ADD COLUMN IF NOT EXISTS embedding JSONB;
            """)
            conn.commit()
            print("✅ Embedding column added successfully")
            
            # Check current state
            cur.execute("SELECT COUNT(*) FROM articles WHERE embedding IS NOT NULL")
            count = cur.fetchone()[0]
            print(f"📊 Articles with embeddings: {count}/307")
            
except Exception as e:
    print(f"❌ Error: {e}")
