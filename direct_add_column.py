import sqlite3
import os

def add_verified_column():
    db_path = 'instance/fuetime.db'
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {os.path.abspath(db_path)}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'verified' in columns:
            print("The 'verified' column already exists in the 'user' table.")
            return
        
        # Add the verified column
        print("Adding 'verified' column to 'user' table...")
        cursor.execute("ALTER TABLE user ADD COLUMN verified BOOLEAN DEFAULT 0")
        conn.commit()
        print("Successfully added 'verified' column to the 'user' table.")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    add_verified_column()
