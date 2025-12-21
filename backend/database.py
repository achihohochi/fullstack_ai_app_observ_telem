import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        raise

def execute_query(query, params=None, fetch=True):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        
        if fetch:
            results = cursor.fetchall()
            conn.commit()
            conn.close()
            return results
        else:
            conn.commit()
            conn.close()
            return None
            
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"ERROR executing query: {e}")
        raise

if __name__ == "__main__":
    print("Testing database connection...")
    try:
        conn = get_db_connection()
        print("✅ SUCCESS: Connected to PostgreSQL!")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM prior_auth_requests")
        result = cursor.fetchone()
        print(f"✅ Found {result['count']} prior auth requests in database")
        conn.close()
    except Exception as e:
        print(f"❌ FAILED: {e}")
