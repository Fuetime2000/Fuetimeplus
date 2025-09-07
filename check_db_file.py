import os
import sys

def main():
    db_path = 'fuetime.db'
    
    # Check if file exists
    if not os.path.exists(db_path):
        print(f"Error: File '{db_path}' does not exist.")
        print(f"Current directory: {os.getcwd()}")
        return 1
    
    # Check file size
    file_size = os.path.getsize(db_path)
    print(f"Database file: {os.path.abspath(db_path)}")
    print(f"File size: {file_size} bytes")
    
    # Check file permissions
    try:
        with open(db_path, 'rb') as f:
            header = f.read(16)
            print(f"File header: {header}")
        print("File is readable.")
    except Exception as e:
        print(f"Error reading file: {e}")
        return 1
    
    # Try to open with sqlite3
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("\nTables in database:")
        for table in tables:
            print(f"- {table[0]}")
            
            # List columns for each table
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        
        return 0
        
    except Exception as e:
        print(f"\nError accessing database: {e}")
        return 1
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    sys.exit(main())
