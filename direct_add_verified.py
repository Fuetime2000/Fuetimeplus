import os
import sqlite3
from pathlib import Path

def add_verified_column():
    # Get the absolute path to the database
    db_path = Path(__file__).parent / 'instance' / 'fuetime.db'
    
    if not db_path.exists():
        print(f"Error: Database file not found at {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
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
        print(f"SQLite Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Attempting to add 'verified' column to user table...")
    if add_verified_column():
        print("\nVerification:")
        try:
            conn = sqlite3.connect('instance/fuetime.db')
            cursor = conn.cursor()
            
            # Verify the column was added
            cursor.execute("PRAGMA table_info(user)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'verified' in columns:
                print("✓ Verified: 'verified' column exists in the database")
                
                # Check the column definition
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user'")
                table_definition = cursor.fetchone()[0]
                if 'verified BOOLEAN' in table_definition.upper():
                    print("✓ Verified: Column is defined as BOOLEAN")
                else:
                    print("✗ Warning: Column definition may not be as expected")
                    print("Table definition snippet:", table_definition[:200] + "...")
            else:
                print("✗ Error: 'verified' column was not added to the database")
                
        except Exception as e:
            print(f"✗ Error during verification: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    else:
        print("Failed to add 'verified' column")
