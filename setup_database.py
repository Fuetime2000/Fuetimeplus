from app import app, db
from models import *  # Import all models to ensure they're registered with SQLAlchemy
import os

def setup_database():
    """Set up the database by creating all tables."""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")

if __name__ == "__main__":
    # Ensure the instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    # Set up the database
    setup_database()
    
    # Verify the tables were created
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    print("\n=== Database Tables ===")
    for table in inspector.get_table_names():
        print(f"- {table}")
