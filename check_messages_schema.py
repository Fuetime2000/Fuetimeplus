import sqlite3
import os

def check_messages_schema():
    db_path = 'fuetime.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found at: {os.path.abspath(db_path)}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        
        print("Messages table columns:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
        
        # Check if read_at column exists
        read_at_exists = any(col[1] == 'read_at' for col in columns)
        
        if not read_at_exists:
            print("\n'read_at' column is missing. Adding it now...")
            try:
                cursor.execute("ALTER TABLE messages ADD COLUMN read_at DATETIME")
                conn.commit()
                print("Successfully added 'read_at' column to messages table.")
            except Exception as e:
                print(f"Error adding column: {e}")
                return False
        else:
            print("\n'read_at' column already exists in messages table.")
            
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if check_messages_schema():
        print("\nDatabase check completed successfully.")
    else:
        print("\nThere was an error checking the database.")
        exit(1)
