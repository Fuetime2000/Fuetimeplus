#!/usr/bin/env python3
"""
Create missing database tables for Socket.IO functionality
"""

from app import app, db
from models import *

def create_missing_tables():
    """Create any missing database tables"""
    with app.app_context():
        try:
            # Import all models to ensure they are registered
            from models import Call, Transaction, Message
            
            # Create all tables
            db.create_all()
            print("✅ All database tables created successfully!")
            
            # Check specific tables
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n📋 Available tables: {len(tables)}")
            for table in sorted(tables):
                print(f"   - {table}")
            
            # Check for required tables
            required_tables = ['user', 'calls', 'transactions', 'messages']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print(f"\n❌ Missing tables: {missing_tables}")
                return False
            else:
                print(f"\n✅ All required tables present!")
                return True
                
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = create_missing_tables()
    if success:
        print("\n🎉 Database setup complete!")
    else:
        print("\n💥 Database setup failed!")
