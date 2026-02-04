import psycopg

conn_string = "postgresql://admin:admin123@postgres:5432/newsdb"
with psycopg.connect(conn_string) as conn:
    with conn.cursor() as cur:
        print("Step 1: Removing duplicates based on (source, title)...")
        
        # Delete duplicates, keeping only the one with the lowest ID
        cur.execute("""
            DELETE FROM articles a
            USING articles b
            WHERE a.id > b.id
            AND a.source = b.source
            AND a.title = b.title
        """)
        
        deleted = cur.rowcount
        conn.commit()
        print(f"  ✓ Deleted {deleted} duplicate articles")
        
        print("\nStep 2: Adding UNIQUE constraint on (source, title)...")
        
        # Drop old constraint if exists
        try:
            cur.execute("ALTER TABLE articles DROP CONSTRAINT IF EXISTS articles_title_unique")
            conn.commit()
        except:
            pass
        
        # Add new constraint
        try:
            cur.execute("""
                ALTER TABLE articles 
                ADD CONSTRAINT unique_source_title UNIQUE (source, title)
            """)
            conn.commit()
            print("  ✓ UNIQUE constraint added successfully")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # Verify
        cur.execute("SELECT COUNT(*) FROM articles")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM (SELECT DISTINCT source, title FROM articles) t")
        unique = cur.fetchone()[0]
        
        print(f"\nFinal verification:")
        print(f"  Total articles: {total}")
        print(f"  Unique (source, title) pairs: {unique}")
        print(f"  Status: {'✓ Clean' if total == unique else '✗ Still has duplicates'}")
