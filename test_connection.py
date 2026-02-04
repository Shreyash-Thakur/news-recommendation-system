import psycopg2
import time

print("Testing PostgreSQL connection...")
print("Waiting for PostgreSQL to be ready...")
time.sleep(5)

try:
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        database='newsdb',
        user='admin',
        password='admin'
    )
    print("✓ Successfully connected to PostgreSQL!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✓ PostgreSQL version: {version[0]}")
    
    cursor.close()
    conn.close()
    print("✓ Connection test passed!")
    
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure Docker is running: docker ps")
    print("2. Check container logs: docker logs news-postgres")
    print("3. Try restarting: docker-compose restart")
