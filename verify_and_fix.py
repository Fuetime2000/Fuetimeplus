import sqlite3
import sys

def verify_and_fix_database():
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
        
        # Get current columns
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print("Current columns in 'messages' table:")
        for col in columns:
            print(f"- {col}")
        
        # Check if read_at column exists
        if 'read_at' not in columns:
            print("\nAdding 'read_at' column to messages table...")
            try:
                cursor.execute("ALTER TABLE messages ADD COLUMN read_at DATETIME")
                conn.commit()
                print("Successfully added 'read_at' column to messages table.")
                
                # Verify the column was added
                cursor.execute("PRAGMA table_info(messages)")
                updated_columns = [col[1] for col in cursor.fetchall()]
                if 'read_at' in updated_columns:
                    print("Verified: 'read_at' column was successfully added.")
                    return True
                else:
                    print("Error: Failed to verify the addition of 'read_at' column.")
                    return False
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
    print("Verifying and fixing database schema...")
    if verify_and_fix_database():
        print("\nDatabase verification and fix completed successfully.")
        sys.exit(0)
    else:
        print("\nFailed to verify or fix the database schema.")
        sys.exit(1)
