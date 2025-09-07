import os
import sqlite3

def check_user_table():
    # Path to the database file
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'fuetime.db')
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at: {db_path}")
        return
    
    print(f"Found database at: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user';")
        if not cursor.fetchone():
            print("❌ 'user' table not found in the database.")
            return
        
        # Get the schema of the user table
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        
        if not columns:
            print("❌ Could not retrieve column information for the 'user' table.")
            return
        
        print("\nColumns in 'user' table:")
        print("-" * 30)
        print(f"{'Name':<20} {'Type':<15} {'Nullable'}")
        print("-" * 30)
        
        verified_exists = False
        for col in columns:
            col_id, name, col_type, notnull, default_val, pk = col
            nullable = "NO" if notnull else "YES"
            print(f"{name:<20} {col_type:<15} {nullable}")
            
            if name == 'verified':
                verified_exists = True
        
        if verified_exists:
            print("\n✅ The 'verified' column exists in the 'user' table!")
        else:
            print("\n❌ The 'verified' column does NOT exist in the 'user' table.")
        
        # Check if there are any users in the database
        try:
            cursor.execute("SELECT COUNT(*) FROM user")
            user_count = cursor.fetchone()[0]
            print(f"\nNumber of users in the database: {user_count}")
        except sqlite3.Error as e:
            print(f"\n❌ Error counting users: {e}")
        
    except sqlite3.Error as e:
        print(f"\n❌ SQLite error: {e}")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_user_table()
