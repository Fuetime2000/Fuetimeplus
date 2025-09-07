import os
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def add_verified_column():
    # Create app with the correct config
    app = create_app()
    
    with app.app_context():
        try:
            # Check if the column already exists
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('user')]
            
            if 'verified' in columns:
                print("✅ The 'verified' column already exists in the 'user' table.")
                return
            
            # Add the verified column
            print("Adding 'verified' column to 'user' table...")
            db.session.execute(text("ALTER TABLE user ADD COLUMN verified BOOLEAN DEFAULT 0"))
            db.session.commit()
            
            print("✅ Successfully added 'verified' column to the 'user' table.")
            
            # Verify the column was added
            result = db.session.execute(text("SELECT verified FROM user LIMIT 1")).fetchone()
            if result is not None:
                print("✅ Verified column is accessible.")
            
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            db.session.rollback()
        finally:
            db.session.close()

if __name__ == "__main__":
    add_verified_column()
