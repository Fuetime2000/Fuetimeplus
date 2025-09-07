import sqlite3
import os

def main():
    db_path = 'fuetime.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file '{db_path}' does not exist.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ No tables found in the database.")
            return
            
        print("Tables in database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Check user table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user';")
        if not cursor.fetchone():
            print("\n❌ 'user' table not found in the database.")
            return
            
        # Get user table columns
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        
        print("\nColumns in 'user' table:")
        verified_exists = False
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
            if col[1] == 'verified':
                verified_exists = True
        
        if verified_exists:
            print("\n✅ The 'verified' column exists in the user table!")
        else:
            print("\n❌ The 'verified' column does NOT exist in the user table.")
        
        # Check alembic version if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version';")
        if cursor.fetchone():
            cursor.execute("SELECT version_num FROM alembic_version LIMIT 1;")
            version = cursor.fetchone()
            if version:
                print(f"\nAlembic version: {version[0]}")
        
    except sqlite3.Error as e:
        print(f"\n❌ SQLite error: {e}")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
