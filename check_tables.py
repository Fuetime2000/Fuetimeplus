from app import app, db
from sqlalchemy import inspect

def check_tables():
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("\n=== Database Tables ===")
        for table in tables:
            print(f"- {table}")
        
        # Check for required tables
        required_tables = ['call', 'transaction']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print("\n[ERROR] Missing required tables:")
            for t in missing_tables:
                print(f"- {t}")
            return False
        
        print("\n[SUCCESS] All required tables exist!")
        return True

if __name__ == "__main__":
    check_tables()
