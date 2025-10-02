from app import app, db
from sqlalchemy import text

def check_database():
    with app.app_context():
        try:
            # Test database connection
            with db.engine.connect() as conn:
                # List all tables in the database
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                
                print("\n=== Database Connection Successful ===")
                print("\n=== Existing Tables in Database ===")
                for row in result:
                    print(f"- {row[0]}")
                
                # Check if user table exists
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'user'
                """))
                
                print("\n=== User Table Columns ===")
                for row in result:
                    print(f"- {row[0]} ({row[1]})")
                
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")

if __name__ == "__main__":
    check_database()
