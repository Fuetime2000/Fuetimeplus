import sqlite3
import os
from pprint import pprint

def check_database():
    db_path = os.path.join(os.path.dirname(__file__), 'fuetime.db')
    
    if not os.path.exists(db_path):
        print(f"Database file not found at: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\n=== Tables in database ===")
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        print("-" * 50)
        
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print("Columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")
        
        # Get index info
        cursor.execute(f"PRAGMA index_list({table_name});")
        indexes = cursor.fetchall()
        
        if indexes:
            print("\nIndexes:")
            for idx in indexes:
                idx_name = idx[1]
                cursor.execute(f"PRAGMA index_info({idx_name});")
                idx_columns = cursor.fetchall()
                col_names = [col[2] for col in idx_columns]
                print(f"  {idx_name}: {', '.join(col_names)}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
