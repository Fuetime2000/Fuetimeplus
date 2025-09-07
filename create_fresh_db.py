import os
from app import create_app, db
from models.user import User

def create_fresh_database():
    # Initialize Flask app
    app = create_app()
    
    with app.app_context():
        # Drop all tables
        print("Dropping all tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating all tables...")
        db.create_all()
        
        # Verify user table has the verified column
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('user')]
        
        if 'verified' in columns:
            print("\n✓ 'verified' column exists in user table")
        else:
            print("\n✗ 'verified' column is MISSING from user table")
        
        print("\nDatabase has been recreated with the latest schema.")

if __name__ == "__main__":
    create_fresh_database()
