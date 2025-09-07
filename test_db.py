import sqlite3
import os

def test_db_connection():
    db_path = 'instance/fuetime.db'
    
    # Check if file exists
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {os.path.abspath(db_path)}")
        return
        
    print(f"Database file exists at: {os.path.abspath(db_path)}")
    print(f"File size: {os.path.getsize(db_path) / (1024*1024):.2f} MB")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
        else:
            print("\nTables in the database:")
            for i, table in enumerate(tables, 1):
                print(f"{i}. {table[0]}")
                
                # Get column info for each table
                try:
                    cursor.execute(f"PRAGMA table_info({table[0]})")
                    columns = cursor.fetchall()
                    print(f"   Columns: {', '.join([col[1] for col in columns])}")
                except Exception as e:
                    print(f"   Error getting columns: {e}")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_db_connection()
