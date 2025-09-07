import os
import sqlite3

def check_verified_column():
    # Path to the SQLite database
    db_path = os.path.join('instance', 'fuetime.db')
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at: {db_path}")
        return
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the 'verified' column exists in the 'user' table
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'verified' in columns:
            print("✅ The 'verified' column exists in the 'user' table!")
            
            # Check if there are any users and if the verified column is set
            cursor.execute("SELECT id, username, verified FROM user LIMIT 5")
            users = cursor.fetchall()
            
            if users:
                print("\nSample users and their verified status:")
                print("-" * 50)
                print(f"{'ID':<5} {'Username':<20} {'Verified'}")
                print("-" * 50)
                for user in users:
                    print(f"{user[0]:<5} {user[1]:<20} {bool(user[2])}")
            else:
                print("\nNo users found in the database.")
        else:
            print("❌ The 'verified' column does not exist in the 'user' table.")
            
            # Show the existing columns for debugging
            print("\nExisting columns in 'user' table:")
            print("-" * 30)
            for col in columns:
                print(f"- {col}")
    
    except sqlite3.Error as e:
        print(f"❌ SQLite error: {e}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_verified_column()
