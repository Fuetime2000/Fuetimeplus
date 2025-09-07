import sqlite3
import os

def list_all_tables():
    db_path = 'instance/fuetime.db'
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {os.path.abspath(db_path)}")
        return
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            return
            
        print(f"Found {len(tables)} tables in the database:")
        print("=" * 50)
        
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * (len(table_name) + 7))
            
            # Get column info
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                if not columns:
                    print("  No columns found")
                    continue
                    
                print("Columns:")
                for col in columns:
                    col_id, name, type_, notnull, default_val, pk = col
                    print(f"  {name} ({type_}){' PRIMARY KEY' if pk else ''}{' NOT NULL' if notnull else ''}{f' DEFAULT {default_val}' if default_val is not None else ''}")
                
                # Count rows
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"\n  Rows: {count:,}")
                
            except Exception as e:
                print(f"  Error getting table info: {e}")
            
            print("\n" + "=" * 50)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    list_all_tables()
