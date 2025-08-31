from app import create_app
from models.user import User
from extensions import db

def test_experience_data():
    app = create_app()
    with app.app_context():
        # Get all users with their experience data
        users = User.query.filter(User.experience.isnot(None)).all()
        print(f"Found {len(users)} users with experience data")
        
        for user in users:
            print(f"User ID: {user.id}, Name: {user.full_name}, Experience: '{user.experience}' (Type: {type(user.experience)})")
            
        # Also check the first user's complete data
        if users:
            user = users[0]
            print("\nSample user data:")
            print(f"ID: {user.id}")
            print(f"Name: {user.full_name}")
            print(f"Email: {user.email}")
            print(f"Experience: '{user.experience}'")
            print(f"Experience Type: {type(user.experience)}")
            print(f"User Type: {user.user_type}")
        else:
            print("No users with experience data found")

if __name__ == "__main__":
    test_experience_data()
