import sqlite3
import sys

def check_database_structure(db_path):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            return
            
        print(f"Found {len(tables)} tables in the database:")
        print("-" * 50)
        
        # Get schema for each table
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * 30)
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            if not columns:
                print("  No columns found")
                continue
                
            print("Columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]}) - {'PRIMARY KEY' if col[5] > 0 else ''}")
            
            # Get row count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"\n  Rows: {count}")
            except Exception as e:
                print(f"  Could not get row count: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    db_path = "instance/fuetime.db"  # Default path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    print(f"Checking database: {db_path}")
    check_database_structure(db_path)
