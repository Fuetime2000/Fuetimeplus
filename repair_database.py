import os
import sys
import sqlite3
import shutil
from datetime import datetime

def backup_database(db_path):
    """Create a backup of the database file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    try:
        shutil.copy2(db_path, backup_path)
        print(f"Database backup created at: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

def check_database_integrity(db_path):
    """Check the integrity of the SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result and result[0] == 'ok':
            print("Database integrity check passed.")
            return True
        else:
            print(f"Database integrity issues found: {result}")
            return False
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_and_fix_schema(db_path):
    """Check and fix the database schema."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if messages table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        if not cursor.fetchone():
            print("Error: 'messages' table not found in the database.")
            return False
            
        # Get table info
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        print("\nColumns in 'messages' table:")
        for col in columns:
            print(f"- {col}")
            
        # Check if read_at column exists
        if 'read_at' not in columns:
            print("\n'read_at' column is missing. Adding it now...")
            try:
                cursor.execute("ALTER TABLE messages ADD COLUMN read_at DATETIME")
                conn.commit()
                print("Successfully added 'read_at' column to messages table.")
                return True
            except Exception as e:
                print(f"Error adding column: {e}")
                return False
        else:
            print("\n'read_at' column already exists in messages table.")
            return True
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    db_path = 'fuetime.db'
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {os.path.abspath(db_path)}")
        return 1
    
    print(f"Database file: {os.path.abspath(db_path)}")
    print(f"File size: {os.path.getsize(db_path) / 1024:.2f} KB")
    
    # Create a backup first
    backup_path = backup_database(db_path)
    if not backup_path:
        print("Failed to create backup. Aborting.")
        return 1
    
    # Check database integrity
    print("\nChecking database integrity...")
    if not check_database_integrity(db_path):
        print("\nDatabase integrity check failed. The database may be corrupted.")
        print(f"A backup has been created at: {backup_path}")
        print("You may need to restore from a known good backup.")
        return 1
    
    # Check and fix schema
    print("\nChecking database schema...")
    if not check_and_fix_schema(db_path):
        print("\nFailed to fix database schema.")
        return 1
    
    print("\nDatabase check and repair completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
