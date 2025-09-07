import os
import sys
import shutil
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

# Database configuration
DATABASE_URI = 'sqlite:///fuetime.db'

def backup_existing_db():
    """Backup the existing database file."""
    if os.path.exists('fuetime.db'):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f'fuetime.db.backup_{timestamp}'
        try:
            shutil.copy2('fuetime.db', backup_path)
            print(f"Backup created: {backup_path}")
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    return True

def init_database():
    """Initialize a new database with the correct schema."""
    # Create a backup of the existing database
    if not backup_existing_db():
        print("Failed to create backup. Aborting.")
        return False
    
    try:
        # Create engine and metadata
        engine = create_engine(DATABASE_URI)
        Base = declarative_base()
        
        # Define the User model
        class User(Base):
            __tablename__ = 'user'
            id = Column(Integer, primary_key=True)
            username = Column(String(80), unique=True, nullable=False)
            email = Column(String(120), unique=True, nullable=False)
            password_hash = Column(String(128))
            is_admin = Column(Boolean, default=False)
            is_active = Column(Boolean, default=True)
            created_at = Column(DateTime, default=datetime.utcnow)
            verified = Column(Boolean, default=False)
        
        # Define the Message model
        class Message(Base):
            __tablename__ = 'messages'
            id = Column(Integer, primary_key=True)
            sender_id = Column(Integer, ForeignKey('user.id'), nullable=False)
            receiver_id = Column(Integer, ForeignKey('user.id'), nullable=False)
            content = Column(Text)
            attachment = Column(String(255))
            is_read = Column(Boolean, default=False)
            created_at = Column(DateTime, default=datetime.utcnow)
            read_at = Column(DateTime, nullable=True)
            
            # Relationships
            sender = relationship('User', foreign_keys=[sender_id], backref='messages_sent')
            receiver = relationship('User', foreign_keys=[receiver_id], backref='messages_received')
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        print("Database initialized successfully.")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    print("Initializing database...")
    if init_database():
        print("Database initialization completed successfully.")
        sys.exit(0)
    else:
        print("Failed to initialize database.")
        sys.exit(1)
