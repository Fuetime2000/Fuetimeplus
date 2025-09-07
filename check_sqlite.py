import os
import sqlite3

def check_database():
    db_path = os.path.join('instance', 'fuetime.db')
    
    if not os.path.exists(db_path):
        print(f"Database file not found at: {os.path.abspath(db_path)}")
        return
        
    print(f"Database found at: {os.path.abspath(db_path)}")
    print(f"File size: {os.path.getsize(db_path) / 1024:.2f} KB")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List all tables
        print("\n=== Tables in database ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(f"- {table[0]}")
        
        # Check user table structure
        if 'user' in [t[0] for t in tables]:
            print("\n=== User table structure ===")
            cursor.execute("PRAGMA table_info(user)")
            for column in cursor.fetchall():
                print(f"{column[1]} ({column[2]}) {'PRIMARY KEY' if column[5] else ''}")
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM user")
        count = cursor.fetchone()[0]
        print(f"\nTotal users in database: {count}")
        
    except sqlite3.Error as e:
        print(f"\nDatabase error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_database()
