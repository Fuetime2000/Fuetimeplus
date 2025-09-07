import os
import sys
import sqlite3

def verify_database():
    db_path = 'fuetime.db'
    
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found.")
        return False
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the database is valid by querying sqlite_master
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("The database is empty (no tables found).")
            return False
            
        print("Tables in the database:")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("Columns:")
            
            # Get column info for each table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        
        return True
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Verifying database...")
    if verify_database():
        print("\nDatabase verification completed successfully.")
        sys.exit(0)
    else:
        print("\nDatabase verification failed.")
        sys.exit(1)
