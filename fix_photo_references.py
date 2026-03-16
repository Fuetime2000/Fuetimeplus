#!/usr/bin/env python3
from app import app, db, User

def check_user_photo_references():
    """Check which users have the problematic filename in their photo field"""
    
    with app.app_context():
        print("=== Checking User Photo References ===\n")
        
        # Find users with the problematic filename
        problematic_filename = "20251209_224222_IMG-251209-183407-35767.jpg"
        new_filename = "20251209_224222_IMG-251209-183407-35767.png"
        
        users_with_old_filename = User.query.filter_by(photo=problematic_filename).all()
        
        if users_with_old_filename:
            print(f"Found {len(users_with_old_filename)} users with the old filename:")
            for user in users_with_old_filename:
                print(f"  - User ID: {user.id}, Name: {user.full_name}, Photo: {user.photo}")
                
                # Update to new filename
                user.photo = new_filename
                print(f"  → Updated to: {user.photo}")
            
            # Commit changes
            db.session.commit()
            print(f"\n✅ Updated {len(users_with_old_filename)} user records")
        else:
            print("No users found with the problematic filename")
        
        # Check all users with photos
        all_users_with_photos = User.query.filter(User.photo.isnot(None)).filter(User.photo != '').all()
        print(f"\nTotal users with photos: {len(all_users_with_photos)}")
        
        for user in all_users_with_photos:
            print(f"  - User {user.id}: {user.photo}")

if __name__ == "__main__":
    check_user_photo_references()
