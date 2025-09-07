import os
import sys
import logging
import time
from app import app, db, User
from werkzeug.security import generate_password_hash
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database with required tables and default data."""
    # Get absolute path to database file
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance/fuetime.db')
    
    # Ensure instance directory exists
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    
    # Try to remove existing database file with retries
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            if os.path.exists(db_file):
                os.remove(db_file)
                logger.info(f"Removed existing database: {db_file}")
                break
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                logger.error(f"Failed to remove existing database after {max_retries} attempts: {e}")
                # Try to continue anyway - the file might be locked but we can still try to use it
                logger.warning("Will attempt to continue with existing database file")
                break
            logger.warning(f"Attempt {attempt + 1} failed to remove database (will retry): {e}")
            time.sleep(retry_delay)

    with app.app_context():
        try:
            logger.info("Creating database tables...")
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully!")
            
            # Create admin user with all required fields
            logger.info("Creating admin user...")
            admin = User(
                email='admin@example.com',
                phone='1234567890',
                full_name='Admin User',
                username='admin',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                work='Administrator',
                experience='5+ years',
                education="Bachelor's Degree",
                is_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                live_location='Main Office',
                current_location='Main Office',
                payment_type='Hourly',
                payment_charge=0.0,
                skills='Administration, Management',
                categories='Administration',
                is_online=False,
                last_active=datetime.utcnow()
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Admin user created successfully!")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    logger.info("Starting database initialization...")
    if init_database():
        logger.info("Database initialization completed successfully!")
    else:
        logger.error("Database initialization failed!")
