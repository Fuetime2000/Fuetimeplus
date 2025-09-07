import os
import sys
from app import app, db
from models.user import User

def fix_verified_column():
    with app.app_context():
        try:
            # Check if the column already exists
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('user')]
            
            if 'verified' in columns:
                print("✓ 'verified' column already exists in the user table")
                return True
                
            # Add the column using raw SQL
            print("Adding 'verified' column to user table...")
            db.session.execute('''
                ALTER TABLE user 
                ADD COLUMN verified BOOLEAN DEFAULT 0 NOT NULL
            ''')
            db.session.commit()
            print("✓ Successfully added 'verified' column to user table")
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            return False
        finally:
            db.session.close()

if __name__ == '__main__':
    if fix_verified_column():
        print("\nVerification:")
        try:
            with app.app_context():
                # Verify the column was added
                inspector = db.inspect(db.engine)
                columns = [column['name'] for column in inspector.get_columns('user')]
                if 'verified' in columns:
                    print("✓ Verification successful: 'verified' column exists in the database")
                    
                    # Check if the column is properly set up in the model
                    if hasattr(User, 'verified'):
                        print("✓ 'verified' attribute is properly defined in the User model")
                    else:
                        print("✗ 'verified' attribute is MISSING from the User model")
                else:
                    print("✗ Verification failed: 'verified' column was not added to the database")
        except Exception as e:
            print(f"✗ Error during verification: {e}")
    else:
        print("Failed to add 'verified' column")
