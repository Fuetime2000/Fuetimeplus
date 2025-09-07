from app import app, db
from models.user import User

with app.app_context():
    # Get the first user to check the columns
    user_columns = [column.name for column in User.__table__.columns]
    print("Columns in User table:")
    for col in user_columns:
        print(f"- {col}")
        
    # Check if 'verified' column exists
    if 'verified' in user_columns:
        print("\n✅ The 'verified' column exists in the User table!")
    else:
        print("\n❌ The 'verified' column does NOT exist in the User table.")
        
    # Count total users
    try:
        user_count = db.session.query(User).count()
        print(f"\nTotal users in database: {user_count}")
    except Exception as e:
        print(f"\nError counting users: {e}")
