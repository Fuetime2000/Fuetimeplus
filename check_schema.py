import sqlite3

def check_schema():
    try:
        # Connect to the SQLite database
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
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            if not columns:
                print("  No columns found")
                continue
                
            print("Columns:")
            for col in columns:
                col_id, name, type_, notnull, default_val, pk = col
                print(f"  {name} ({type_}){' PRIMARY KEY' if pk else ''}{' NOT NULL' if notnull else ''}{f' DEFAULT {default_val}' if default_val is not None else ''}")
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_schema()
