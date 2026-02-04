import psycopg

conn_string = "postgresql://admin:admin123@postgres:5432/newsdb"
with psycopg.connect(conn_string) as conn:
    with conn.cursor() as cur:
        # Check for duplicate titles
        cur.execute("""
            SELECT title, COUNT(*) as count 
            FROM articles 
            GROUP BY title 
            HAVING COUNT(*) > 1 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        """)
        
        print("Duplicate articles found:")
        duplicates = cur.fetchall()
        if duplicates:
            for title, count in duplicates:
                print(f"  {count}x: {title[:80]}")
        else:
            print("  No duplicates found")
        
        # Get total unique vs total articles
        cur.execute("SELECT COUNT(*) FROM articles")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT title) FROM articles")
        unique = cur.fetchone()[0]
        
        print(f"\nTotal articles: {total}")
        print(f"Unique titles: {unique}")
        print(f"Duplicates: {total - unique}")
