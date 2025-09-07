import sqlite3
import sys

def check_and_fix_schema():
    db_path = 'fuetime.db'
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if messages table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        if not cursor.fetchone():
            print("Error: 'messages' table not found in the database.")
            return False
        
        # Check if read_at column exists in messages table
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print("Current columns in 'messages' table:")
        for col in columns:
            print(f"- {col}")
        
        if 'read_at' not in columns:
            print("\nAdding 'read_at' column to messages table...")
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
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Checking and fixing database schema...")
    if check_and_fix_schema():
        print("\nDatabase schema check and fix completed successfully.")
        sys.exit(0)
    else:
        print("\nFailed to fix database schema.")
        sys.exit(1)
