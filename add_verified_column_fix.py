import os
import sqlite3

def add_verified_column():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'fuetime.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'verified' in columns:
            print("✓ 'verified' column already exists in the user table")
            return True
            
        # Add the column
        print("Adding 'verified' column to user table...")
        cursor.execute("""
            ALTER TABLE user 
            ADD COLUMN verified BOOLEAN DEFAULT 0 NOT NULL
        """)
        
        conn.commit()
        print("✓ Successfully added 'verified' column to user table")
        return True
        
    except sqlite3.Error as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if add_verified_column():
        print("\nVerifying the change...")
        # Verify the column was added
        try:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'fuetime.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT verified FROM user LIMIT 1")
            print("✓ Verified: The 'verified' column is accessible")
        except sqlite3.Error as e:
            print(f"✗ Verification failed: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    else:
        print("Failed to add 'verified' column")
