import os
import sqlite3
from app import app

def check_messages_schema():
    # Get the database path from the app config
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    print(f"Checking database at: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Database file not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        
        print("\nMessages table columns:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
        
        # Check if read_at column exists
        read_at_exists = any(col[1] == 'read_at' for col in columns)
        
        if not read_at_exists:
            print("\n'read_at' column is missing. Adding it now...")
            try:
                cursor.execute("ALTER TABLE messages ADD COLUMN read_at DATETIME")
                conn.commit()
                print("✅ Successfully added 'read_at' column to messages table.")
            except Exception as e:
                print(f"❌ Error adding column: {e}")
                return False
        else:
            print("\n✅ 'read_at' column already exists in messages table.")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    with app.app_context():
        print("Starting database schema check...")
        if check_messages_schema():
            print("\n✅ Database check completed successfully.")
        else:
            print("\n❌ There was an error checking/updating the database schema.")
