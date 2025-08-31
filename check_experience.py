from flask import Flask
from models.user import User
from extensions import db
import os

def check_experience_data():
    # Create a minimal Flask app
    app = Flask(__name__)
    
    # Configure the database
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance/fuetime.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    with app.app_context():
        # Get all users with their experience data
        users = User.query.filter(User.experience.isnot(None)).all()
        print(f"Found {len(users)} users with experience data")
        
        for user in users[:5]:  # Show first 5 users with experience
            print(f"User ID: {user.id}, Name: {user.full_name}, Experience: '{user.experience}' (Type: {type(user.experience)})")
        
        # Also show first 5 users regardless of experience
        all_users = User.query.limit(5).all()
        print("\nFirst 5 users in the database:")
        for user in all_users:
            print(f"ID: {user.id}, Name: {user.full_name}, Experience: '{user.experience}', Type: {user.user_type}")

if __name__ == "__main__":
    check_experience_data()
