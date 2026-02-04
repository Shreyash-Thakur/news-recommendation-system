import psycopg

conn_string = "postgresql://admin:admin123@postgres:5432/newsdb"
with psycopg.connect(conn_string) as conn:
    with conn.cursor() as cur:
        print("Removing duplicate articles...")
        
        # Delete duplicates, keeping only the one with the lowest ID
        cur.execute("""
            DELETE FROM articles a
            USING articles b
            WHERE a.id > b.id
            AND a.title = b.title
        """)
        
        deleted = cur.rowcount
        conn.commit()
        
        print(f"Deleted {deleted} duplicate articles")
        
        # Check final count
        cur.execute("SELECT COUNT(*) FROM articles")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT title) FROM articles")
        unique = cur.fetchone()[0]
        
        print(f"\nFinal count:")
        print(f"  Total articles: {total}")
        print(f"  Unique titles: {unique}")
        print(f"  Remaining duplicates: {total - unique}")
