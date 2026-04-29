import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'hiring_system.db')

def fix_schema():
    print(f"Fixing schema for {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Add skills column to jobs
    try:
        cursor.execute('ALTER TABLE jobs ADD COLUMN skills TEXT')
        print("Added 'skills' column to 'jobs' table.")
    except sqlite3.OperationalError as e:
        print(f"Skipping 'skills': {e}")
        
    # Add experience_required column to jobs
    try:
        cursor.execute('ALTER TABLE jobs ADD COLUMN experience_required INTEGER DEFAULT 0')
        print("Added 'experience_required' column to 'jobs' table.")
    except sqlite3.OperationalError as e:
        print(f"Skipping 'experience_required': {e}")
        
    conn.commit()
    conn.close()
    print("Schema fix complete.")

if __name__ == "__main__":
    fix_schema()
