import sqlite3

def list_tables(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            return
            
        print(f"Found {len(tables)} tables:")
        print("=" * 50)
        
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * (len(table_name) + 8))
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            if not columns:
                print("  No columns found")
                continue
                
            print("Columns:")
            for col in columns:
                col_id, name, type_, notnull, default_value, pk = col
                print(f"  {name} ({type_}){' PRIMARY KEY' if pk else ''}{' NOT NULL' if notnull else ''}{f' DEFAULT {default_value}' if default_value is not None else ''}")
            
            # Count rows
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"\n  Rows: {count:,}")
            except Exception as e:
                print(f"\n  Could not count rows: {e}")
            
            print("\n" + "=" * 50)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import sys
    db_path = "instance/fuetime.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    list_tables(db_path)
