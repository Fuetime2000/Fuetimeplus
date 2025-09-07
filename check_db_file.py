import os
import sqlite3

def check_database_file():
    db_path = os.path.join('instance', 'fuetime.db')
    
    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at: {os.path.abspath(db_path)}")
        print("\nPlease run the following command to initialize the database:")
        print("flask db upgrade")
        return False
    
    print(f"✅ Database file found at: {os.path.abspath(db_path)}")
    print(f"File size: {os.path.getsize(db_path) / 1024:.2f} KB")
    
    # Try to connect to the database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if not cursor.fetchone():
            print("❌ 'user' table not found in the database")
            return False
        
        print("✅ 'user' table exists")
        
        # Check if verified column exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'verified' in columns:
            print("✅ 'verified' column exists in 'user' table")
        else:
            print("❌ 'verified' column is MISSING from 'user' table")
            return False
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== Database File Check ===\n")
    if check_database_file():
        print("\n✅ Database check completed successfully!")
    else:
        print("\n❌ Database check found issues that need to be resolved.")
