import sqlite3
import sys

def fix_read_at_column():
    db_path = 'fuetime.db'
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Found tables: {', '.join(tables)}")
        
        if 'messages' not in tables:
            print("Error: 'messages' table not found in the database.")
            return False
        
        # Check if read_at column exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Columns in 'messages' table: {', '.join(columns)}")
        
        if 'read_at' not in columns:
            print("Adding 'read_at' column to 'messages' table...")
            try:
                cursor.execute("ALTER TABLE messages ADD COLUMN read_at DATETIME")
                conn.commit()
                print("Successfully added 'read_at' column.")
                
                # Verify the column was added
                cursor.execute("PRAGMA table_info(messages)")
                updated_columns = [column[1] for column in cursor.fetchall()]
                if 'read_at' in updated_columns:
                    print("Verified: 'read_at' column was successfully added.")
                    return True
                else:
                    print("Error: Failed to verify the addition of 'read_at' column.")
                    return False
            except sqlite3.Error as e:
                print(f"Error adding column: {e}")
                return False
        else:
            print("'read_at' column already exists in 'messages' table.")
            return True
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Fixing 'read_at' column in messages table...")
    if fix_read_at_column():
        print("\nDatabase fix completed successfully.")
        sys.exit(0)
    else:
        print("\nFailed to fix the database.")
        sys.exit(1)
