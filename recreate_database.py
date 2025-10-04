"""
Script to safely drop and recreate the database with all tables.
Run this script with: python recreate_database.py
"""
import os
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import SQLAlchemy and models
from extensions import db
from models.user import User
from models.message import Message
from models.review import Review
from models.contact_request import ContactRequest
from models.user_interaction import UserInteraction
from models.job_posting import JobPosting
from models.job_request import JobRequest

def recreate_database():
    """Drop and recreate all database tables."""
    try:
        # Get the database path
        db_path = Path('instance/fuetime.db')
        
        # Create instance directory if it doesn't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup the existing database if it exists
        if db_path.exists():
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = db_path.with_name(f'fuetime.db.backup_{timestamp}')
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"[OK] Created backup at: {backup_path}")
        
        # Initialize the app with the database
        from app import app
        
        with app.app_context():
            print("Dropping all tables...")
            db.drop_all()
            print("Creating all tables...")
            db.create_all()
            print("[OK] Database recreated successfully!")
            
    except Exception as e:
        print(f"[ERROR] Error recreating database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    return True

if __name__ == '__main__':
    print("=== Database Recreation Tool ===")
    print("WARNING: This will delete all data in the database!")
    print("Proceeding with database recreation...")
    
    if recreate_database():
        print("\nNext steps:")
        print("1. Run 'flask db upgrade' to apply any pending migrations")
        print("2. Restart your Flask application")
    else:
        print("\nFailed to recreate the database. Please check the error messages above.")
