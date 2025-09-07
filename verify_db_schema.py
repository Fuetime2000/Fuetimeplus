import sqlite3

def check_table_columns():
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('instance/fuetime.db')
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("=== Database Tables ===")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * 50)
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Print column details
            for col in columns:
                col_id, col_name, col_type, notnull, default_val, is_pk = col
                print(f"{col_name}: {col_type} {'PRIMARY KEY' if is_pk else ''} {'NOT NULL' if notnull else ''} {'DEFAULT ' + str(default_val) if default_val is not None else ''}")
        
        # Check for required columns in user table
        cursor.execute("PRAGMA table_info(user)")
        user_columns = [col[1] for col in cursor.fetchall()]
        
        print("\n=== Required Columns Check ===")
        required_columns = ['verified', 'email', 'password_hash']
        for col in required_columns:
            if col in user_columns:
                print(f"✓ Column '{col}' exists in user table")
            else:
                print(f"✗ Column '{col}' is MISSING from user table")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_table_columns()
