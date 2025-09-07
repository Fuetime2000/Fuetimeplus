import os
import sys

def find_database():
    # Common database locations to check
    possible_paths = [
        'fuetime.db',
        'instance/fuetime.db',
        'app.db',
        'instance/app.db',
        'database.db',
        'instance/database.db',
        os.path.join(os.path.dirname(__file__), 'fuetime.db'),
        os.path.join(os.path.dirname(__file__), 'instance/fuetime.db')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    return None

def fix_database(db_path):
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if messages table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        if not cursor.fetchone():
            print(f"Error: 'messages' table not found in {db_path}")
            return False
        
        # Check if read_at column exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'read_at' not in columns:
            print("Adding 'read_at' column to messages table...")
            try:
                cursor.execute("ALTER TABLE messages ADD COLUMN read_at DATETIME")
                conn.commit()
                print("Successfully added 'read_at' column to messages table.")
                return True
            except Exception as e:
                print(f"Error adding column: {e}")
                return False
        else:
            print("'read_at' column already exists in messages table.")
            return True
            
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Searching for database file...")
    db_path = find_database()
    
    if not db_path:
        print("Error: Could not find database file.")
        print("Please specify the path to your database file as an argument.")
        print("Example: python direct_db_fix.py /path/to/your/database.db")
        sys.exit(1)
    
    print(f"Found database at: {db_path}")
    if fix_database(db_path):
        print("Database check completed successfully.")
        sys.exit(0)
    else:
        print("There was an error updating the database.")
        sys.exit(1)
