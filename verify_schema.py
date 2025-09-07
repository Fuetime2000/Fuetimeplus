import sqlite3

def main():
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('fuetime.db')
        cursor = conn.cursor()
        
        # Get all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Check if user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user';")
        if not cursor.fetchone():
            print("\n❌ User table does not exist in the database.")
            return
            
        # Get user table structure
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        
        print("\nColumns in user table:")
        verified_exists = False
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
            if col[1] == 'verified':
                verified_exists = True
        
        if verified_exists:
            print("\n✅ The 'verified' column exists in the user table!")
        else:
            print("\n❌ The 'verified' column does NOT exist in the user table.")
        
        # Check alembic version
        try:
            cursor.execute("SELECT version_num FROM alembic_version LIMIT 1")
            version = cursor.fetchone()
            if version:
                print(f"\nAlembic version: {version[0]}")
            else:
                print("\nAlembic version not found")
        except sqlite3.OperationalError:
            print("\nAlembic version table does not exist")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
