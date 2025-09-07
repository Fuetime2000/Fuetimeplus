from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

# Create a minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/fuetime.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Import your models after initializing db to avoid circular imports
from models.user import User

# Initialize Flask-Migrate
migrate = Migrate(app, db)

def create_migration():
    with app.app_context():
        # Create migrations directory if it doesn't exist
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        if not os.path.exists(migrations_dir):
            os.makedirs(migrations_dir)
            print("Created migrations directory")
        
        # Initialize the database if needed
        db.create_all()
        
        # Create a migration
        from flask_migrate import upgrade, migrate as migrate_cmd, init, stamp
        
        # Initialize migrations if not already done
        if not os.path.exists(os.path.join(migrations_dir, 'env.py')):
            print("Initializing migrations...")
            init()
            
        # Create a new migration
        print("Creating migration...")
        migrate_cmd(message='Add verified column to user table')
        
        # Apply the migration
        print("Applying migration...")
        upgrade()
        
        print("Migration completed successfully!")

if __name__ == '__main__':
    create_migration()
