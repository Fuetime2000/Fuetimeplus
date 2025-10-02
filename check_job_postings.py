from app import app, db
from sqlalchemy import text

def check_job_postings_table():
    with app.app_context():
        try:
            # Check if the table exists
            with db.engine.connect() as conn:
                # For SQLite
                result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='job_postings'"
                ))
                table_exists = result.fetchone()
                
                if table_exists:
                    print("✅ job_postings table exists!")
                    
                    # Get table info
                    result = conn.execute(text("PRAGMA table_info(job_postings)"))
                    columns = result.fetchall()
                    
                    print("\nTable structure:")
                    print("-" * 50)
                    for col in columns:
                        print(f"- {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
                else:
                    print("❌ job_postings table does not exist!")
                    
                    # List all tables for debugging
                    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                    tables = [row[0] for row in result.fetchall()]
                    print("\nExisting tables:", ", ".join(tables) if tables else "No tables found")
                    
        except Exception as e:
            print(f"Error checking database: {str(e)}")

if __name__ == "__main__":
    check_job_postings_table()
