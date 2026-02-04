"""
Generate embeddings for all articles using SentenceTransformer.
Run this ONCE after adding the embedding column.
Caches embeddings in database for fast retrieval.
"""

import psycopg
import json
from sentence_transformers import SentenceTransformer

# Database connection
conn_string = "postgresql://admin:admin123@postgres:5432/newsdb"

print("🔄 Loading SentenceTransformer model (all-MiniLM-L6-v2)...")
model = SentenceTransformer("all-MiniLM-L6-v2")  # 384 dimensions, fast
print("✅ Model loaded")

try:
    with psycopg.connect(conn_string) as conn:
        with conn.cursor() as cur:
            # Fetch all articles without embeddings
            cur.execute("""
                SELECT id, title, content, category 
                FROM articles 
                WHERE embedding IS NULL
            """)
            articles = cur.fetchall()
            
            if not articles:
                print("✅ All articles already have embeddings")
                exit(0)
            
            print(f"📝 Generating embeddings for {len(articles)} articles...")
            
            for i, (article_id, title, content, category) in enumerate(articles, 1):
                # Combine title + content (weight title more)
                text = f"{title}. {title}. {title}. {content or ''}"
                
                # Generate embedding
                embedding = model.encode(text, show_progress_bar=False)
                
                # Convert to JSON-serializable list
                embedding_json = json.dumps(embedding.tolist())
                
                # Store in database
                cur.execute("""
                    UPDATE articles 
                    SET embedding = %s::jsonb 
                    WHERE id = %s
                """, (embedding_json, article_id))
                
                if i % 50 == 0:
                    print(f"  Progress: {i}/{len(articles)} articles processed")
                    conn.commit()
            
            conn.commit()
            print(f"✅ Generated embeddings for {len(articles)} articles")
            
            # Verify
            cur.execute("SELECT COUNT(*) FROM articles WHERE embedding IS NOT NULL")
            count = cur.fetchone()[0]
            print(f"📊 Total articles with embeddings: {count}/307")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
