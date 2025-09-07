import sqlite3

def check_columns():
    try:
        conn = sqlite3.connect('instance/fuetime.db')
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("Tables in the database:")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * (len(table_name) + 7))
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            if not columns:
                print("  No columns found")
                continue
                
            print("Columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]}){' PRIMARY KEY' if col[5] else ''}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_columns()
