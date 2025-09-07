import sqlite3
import sys

def check_and_fix_read_at():
    db_path = 'fuetime.db'
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'read_at' not in columns:
            print("Column 'read_at' is missing from 'messages' table. Adding it now...")
            try:
                # Add the column
                cursor.execute("ALTER TABLE messages ADD COLUMN read_at DATETIME")
                conn.commit()
                print("Successfully added 'read_at' column to 'messages' table.")
            except sqlite3.Error as e:
                print(f"Error adding 'read_at' column: {e}")
                return False
        else:
            print("'read_at' column already exists in 'messages' table.")
        
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if check_and_fix_read_at():
        sys.exit(0)
    else:
        sys.exit(1)
