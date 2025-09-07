from models.user import User

print("User model columns:")
for column in User.__table__.columns:
    print(f"- {column.name} ({column.type})")

# Check if 'verified' column exists in the model
has_verified = any(column.name == 'verified' for column in User.__table__.columns)
print("\n'verified' column exists in model:", "✅ Yes" if has_verified else "❌ No")
