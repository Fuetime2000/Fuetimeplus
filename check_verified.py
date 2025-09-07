from app import app, db
from models.user import User

def check_verified_column():
    with app.app_context():
        # Check if the column exists in the model
        if hasattr(User, 'verified'):
            print("✅ 'verified' column exists in the User model")
        else:
            print("❌ 'verified' column does not exist in the User model")
            return
        
        # Try to query the column
        try:
            # This will fail if the column doesn't exist in the database
            user = db.session.query(User).first()
            if user is not None:
                print(f"✅ Successfully queried User table. Verified status: {user.verified}")
            else:
                print("ℹ️ No users found in the database")
        except Exception as e:
            if "no such column: user.verified" in str(e):
                print("❌ 'verified' column does not exist in the database")
            else:
                print(f"❌ Error querying User table: {e}")

if __name__ == "__main__":
    check_verified_column()
