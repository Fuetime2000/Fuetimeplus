from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/fuetime.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'temporary-secret-key-for-db-operations'
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    
    return app

def add_verified_column():
    app = create_app()
    
    with app.app_context():
        try:
            # Check if the column already exists
            result = db.session.execute(
                "SELECT name FROM pragma_table_info('user') WHERE name='verified'"
            ).fetchone()
            
            if result:
                print("✓ 'verified' column already exists in the user table")
                return True
                
            # Add the column
            print("Adding 'verified' column to user table...")
            db.session.execute('''
                ALTER TABLE user 
                ADD COLUMN verified BOOLEAN DEFAULT 0 NOT NULL
            ''')
            db.session.commit()
            print("✓ Successfully added 'verified' column to user table")
            
            # Verify the column was added
            result = db.session.execute(
                "SELECT name FROM pragma_table_info('user') WHERE name='verified'"
            ).fetchone()
            
            if result:
                print("✓ Verification successful: 'verified' column exists in the database")
                return True
            else:
                print("✗ Error: Failed to verify column addition")
                return False
                
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            return False
        finally:
            db.session.close()

if __name__ == "__main__":
    if add_verified_column():
        print("\nOperation completed successfully!")
    else:
        print("\nFailed to add 'verified' column")
