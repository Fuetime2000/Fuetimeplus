import os
import sqlite3
from app import app

def verify_database():
    db_path = os.path.join('instance', 'fuetime.db')
    
    if not os.path.exists(db_path):
        print("✗ Database file not found")
        return False
    
    print(f"✓ Database found at: {os.path.abspath(db_path)}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if not cursor.fetchone():
            print("✗ 'user' table not found")
            return False
        print("✓ 'user' table exists")
        
        # Check if verified column exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'verified' in columns:
            print("✓ 'verified' column exists in 'user' table")
        else:
            print("✗ 'verified' column is missing from 'user' table")
            return False
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM user")
        count = cursor.fetchone()[0]
        print(f"✓ Found {count} user(s) in the database")
        
        # Check for admin user
        cursor.execute("SELECT username, email, is_admin, verified FROM user WHERE username = 'admin'")
        admin = cursor.fetchone()
        if admin:
            print(f"✓ Admin user found: {admin[0]} ({admin[1]})")
            print(f"   is_admin: {bool(admin[2])}, verified: {bool(admin[3])}")
        else:
            print("✗ Admin user not found")
            return False
        
        return True
        
    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=== Database Verification ===\n")
    if verify_database():
        print("\n✓ Database verification successful!")
    else:
        print("\n✗ Database verification failed")
