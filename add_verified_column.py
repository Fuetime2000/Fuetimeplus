import sqlite3

def add_verified_column():
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('instance/fuetime.db')
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'verified' in columns:
            print("The 'verified' column already exists in the 'user' table.")
            return
        
        # Add the verified column
        cursor.execute("ALTER TABLE user ADD COLUMN verified BOOLEAN DEFAULT 0")
        conn.commit()
        print("Successfully added 'verified' column to the 'user' table.")
        
        # Verify the column was added
        cursor.execute("SELECT verified FROM user LIMIT 1")
        print("Verified column exists and is accessible.")
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_verified_column()
