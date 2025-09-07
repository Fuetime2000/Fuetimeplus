import sqlite3
import sys

def add_verified_column():
    conn = None
    try:
        # Connect to the SQLite database
        db_path = 'instance/fuetime.db'
        print(f"Connecting to database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'verified' in columns:
            print("✓ 'verified' column already exists in the 'user' table")
            return True
        
        # Add the verified column with a default value of 0 (False)
        print("Adding 'verified' column to 'user' table...")
        cursor.execute("""
        ALTER TABLE user 
        ADD COLUMN verified BOOLEAN NOT NULL DEFAULT 0
        """)
        
        # Commit the changes
        conn.commit()
        print("✓ Successfully added 'verified' column to the 'user' table")
        return True
        
    except sqlite3.Error as e:
        print(f"Error: {e}", file=sys.stderr)
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=== Verifying Database Schema ===")
    if add_verified_column():
        print("\nDatabase verification and update completed successfully!")
    else:
        print("\nFailed to update database schema.", file=sys.stderr)
        sys.exit(1)
