import sqlite3

def check_columns():
    conn = sqlite3.connect('fuetime.db')
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("PRAGMA table_info('user')")
    columns = cursor.fetchall()
    
    print("Columns in 'user' table:")
    for col in columns:
        print(f"- {col[1]} (Type: {col[2]}, Nullable: {not col[3]}, Default: {col[4]})")
    
    # Check if 'verified' column exists
    verified_exists = any('verified' in col for col in columns)
    if verified_exists:
        print("\n✅ The 'verified' column exists in the User table!")
    else:
        print("\n❌ The 'verified' column does NOT exist in the User table.")
    
    # Check alembic version
    try:
        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()
        print(f"\nAlembic version: {version[0] if version else 'Not found'}")
    except sqlite3.OperationalError:
        print("\nAlembic version table not found")
    
    conn.close()

if __name__ == "__main__":
    check_columns()
