from app import app, db
from models.user import User
from datetime import datetime

def add_verified_column():
    with app.app_context():
        try:
            # Create a new migration
            from flask_migrate import upgrade
            
            print("Creating and applying migration to add 'verified' column...")
            
            # Create a new migration file
            from alembic import op
            import sqlalchemy as sa
            
            # Add the verified column with a default value of False
            op.add_column('user', sa.Column('verified', sa.Boolean(), nullable=False, server_default='0'))
            
            print("✓ Successfully added 'verified' column to 'user' table")
            
            # Update existing users to have verified=True if needed
            # User.query.update({'verified': True})
            # db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return False

if __name__ == "__main__":
    print("=== Adding 'verified' column to user table ===\n")
    if add_verified_column():
        print("\n✓ Database update completed successfully!")
    else:
        print("\n✗ Failed to update database.")
