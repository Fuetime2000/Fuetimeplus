import os
import sqlite3
import sys

def fix_missing_read_at(db_path):
    """Check and fix the missing read_at column in the messages table."""
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if messages table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        if not cursor.fetchone():
            print("Error: 'messages' table not found in the database.")
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

def main():
    db_path = os.path.abspath('fuetime.db')
    print(f"Checking database at: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return 1
    
    if fix_missing_read_at(db_path):
        print("Database schema check completed successfully.")
        return 0
    else:
        print("There was an error updating the database schema.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
