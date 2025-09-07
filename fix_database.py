import os
import sys
import sqlite3

def check_database():
    db_path = 'fuetime.db'
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {os.path.abspath(db_path)}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if messages table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        if not cursor.fetchone():
            print("Error: 'messages' table not found in the database.")
            return False
            
        # Get table info
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        print("Columns in 'messages' table:")
        for col in columns:
            print(f"- {col}")
            
        # Check if read_at column exists
        if 'read_at' not in columns:
            print("\n'read_at' column is missing. Adding it now...")
            try:
                cursor.execute("ALTER TABLE messages ADD COLUMN read_at DATETIME")
                conn.commit()
                print("Successfully added 'read_at' column to messages table.")
                return True
            except Exception as e:
                print(f"Error adding column: {e}")
                return False
        else:
            print("\n'read_at' column already exists in messages table.")
            return True
            
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    print("Checking database schema...")
    if check_database():
        print("\nDatabase check completed successfully.")
        return 0
    else:
        print("\nThere was an error checking the database.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
