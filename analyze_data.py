import psycopg

conn_string = "postgresql://admin:admin123@postgres:5432/newsdb"
with psycopg.connect(conn_string) as conn:
    with conn.cursor() as cur:
        # Check content availability
        cur.execute("SELECT COUNT(*) FROM articles WHERE content IS NOT NULL AND content != ''")
        with_content = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM articles")
        total = cur.fetchone()[0]
        
        print(f"Data Quality Analysis:")
        print(f"  Total articles: {total}")
        print(f"  With content: {with_content}")
        print(f"  Without content: {total - with_content}")
        print(f"  Content coverage: {(with_content/total*100):.1f}%")
        
        # Average content length
        cur.execute("""
            SELECT AVG(LENGTH(content)) 
            FROM articles 
            WHERE content IS NOT NULL AND content != ''
        """)
        avg_length = cur.fetchone()[0]
        print(f"  Average content length: {avg_length:.0f} chars")
        
        # Check by category
        print(f"\nArticles per category:")
        cur.execute("""
            SELECT category, COUNT(*) as count
            FROM articles
            GROUP BY category
            ORDER BY count DESC
        """)
        for cat, count in cur.fetchall():
            print(f"    {cat}: {count}")
