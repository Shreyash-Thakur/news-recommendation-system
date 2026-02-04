import psycopg

conn_string = "postgresql://admin:admin123@postgres:5432/newsdb"
with psycopg.connect(conn_string) as conn:
    with conn.cursor() as cur:
        print("Adding unique constraint on article titles...")
        
        try:
            cur.execute("""
                ALTER TABLE articles 
                ADD CONSTRAINT articles_title_unique UNIQUE (title)
            """)
            conn.commit()
            print("✓ Unique constraint added successfully")
        except Exception as e:
            print(f"Note: {e}")
            print("Constraint may already exist or there are duplicates")
