from app import app, db
from sqlalchemy import inspect

def add_verified_column():
    with app.app_context():
        try:
            # Create an inspector to check the database
            inspector = inspect(db.engine)
            
            # Check if the 'user' table exists
            if 'user' not in inspector.get_table_names():
                print("Error: 'user' table does not exist in the database.")
                return False
            
            # Check if 'verified' column already exists
            columns = [col['name'] for col in inspector.get_columns('user')]
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

if __name__ == "__main__":
    if add_verified_column():
        print("\nVerification:")
        try:
            with app.app_context():
                # Verify the column was added
                inspector = inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('user')]
                if 'verified' in columns:
                    print("✓ Verification successful: 'verified' column exists in the database")
                    
                    # Check the column definition
                    result = db.session.execute(
                        "SELECT sql FROM sqlite_master WHERE type='table' AND name='user'"
                    ).scalar()
                    if 'verified BOOLEAN' in result.upper():
                        print("✓ Verified: Column is defined as BOOLEAN")
                    else:
                        print("✗ Warning: Column definition may not be as expected")
                        print(f"Table definition: {result[:200]}...")
                else:
                    print("✗ Error: 'verified' column was not added to the database")
        except Exception as e:
            print(f"✗ Error during verification: {e}")
    else:
        print("Failed to add 'verified' column")
