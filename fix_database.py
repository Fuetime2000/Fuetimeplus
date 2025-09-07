import os
import sys
import shutil
from datetime import datetime
from app import app, db
from models.user import User
from werkzeug.security import generate_password_hash

def backup_database():
    """Create a backup of the current database."""
    src = os.path.join('instance', 'fuetime.db')
    if not os.path.exists(src):
        print("No existing database to back up.")
        return True
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join('instance', f'fuetime_backup_{timestamp}.db')
    
    try:
        shutil.copy2(src, dst)
        print(f"✓ Database backed up to: {dst}")
        return True
    except Exception as e:
        print(f"✗ Failed to back up database: {e}")
        return False

def reset_database():
    """Reset the database by removing and recreating it."""
    db_path = os.path.join('instance', 'fuetime.db')
    
    # Remove existing database file
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("✓ Removed existing database")
        except Exception as e:
            print(f"✗ Failed to remove database: {e}")
            return False
    
    # Create all tables
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("✓ Database tables created successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to create database tables: {e}")
            return False

def create_admin_user():
    """Create an admin user."""
    with app.app_context():
        try:
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                full_name='Admin User',
                is_admin=True,
                verified=True,
                phone='1234567890',
                work='Administrator',
                experience='5+ years',
                education="Bachelor's Degree"
            )
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin user created successfully")
            print("   Username: admin")
            print("   Password: admin123")
            return True
        except Exception as e:
            print(f"✗ Failed to create admin user: {e}")
            return False

if __name__ == "__main__":
    print("=== Database Reset Tool ===\n")
    
    # Backup existing database
    print("1. Backing up existing database...")
    if not backup_database():
        print("\n! Warning: Could not back up database. Continue anyway? (y/n) ")
        if input().lower() != 'y':
            print("\nOperation cancelled.")
            sys.exit(1)
    
    # Reset database
    print("\n2. Resetting database...")
    if not reset_database():
        print("\n✗ Failed to reset database")
        sys.exit(1)
    
    # Create admin user
    print("\n3. Creating admin user...")
    create_admin_user()
    
    print("\n✓ Database reset completed successfully!")
