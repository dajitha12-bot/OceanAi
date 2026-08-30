import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load env variables
load_dotenv()

def verify_database_extensions():
    db_url = os.getenv('DATABASE_URL', 'postgres://postgres:postgres@localhost:5432/ocean_intelligence')
    
    # Replace postgis:// with postgresql:// for psycopg2 driver compatibility
    if db_url.startswith('postgis://'):
        db_url = db_url.replace('postgis://', 'postgresql://', 1)
        
    print(f"Connecting to: {db_url.split('@')[-1]} (password masked)")
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        print("SUCCESS: Database connection successful.")
        
        # 1. Check PostGIS
        try:
            cursor.execute("SELECT PostGIS_Version();")
            version = cursor.fetchone()[0]
            print(f"INFO: PostGIS is active. Version: {version}")
        except Exception:
            print("ERROR: PostGIS extension is NOT active or NOT installed.")
            print("   Fix: Run 'CREATE EXTENSION IF NOT EXISTS postgis;' in the database.")
            
        # 2. Check pgvector
        try:
            cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
            res = cursor.fetchone()
            if res:
                print(f"INFO: pgvector is active. Version: {res[0]}")
            else:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                print("SUCCESS: pgvector extension created successfully.")
        except Exception as e:
            print("ERROR: pgvector extension is NOT active or NOT installed.")
            print(f"   Error: {e}")
            print("   Fix: Ensure pgvector is compiled on your PostgreSQL server and run 'CREATE EXTENSION IF NOT EXISTS vector;'.")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print("ERROR: Database connection failed.")
        print(f"   Error detail: {e}")
        print("   Ensure PostgreSQL is running and the credentials in DATABASE_URL are correct.")

if __name__ == "__main__":
    verify_database_extensions()