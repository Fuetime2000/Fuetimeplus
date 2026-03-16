#!/usr/bin/env python3
import os
import requests
from app import app

def test_profile_images():
    """Test profile image serving and identify potential issues"""
    
    with app.app_context():
        print("=== Profile Image Diagnostic ===\n")
        
        # Check upload directories
        upload_dir = os.path.join(app.root_path, 'static', 'uploads')
        profile_pics_dir = os.path.join(upload_dir, 'profile_pics')
        
        print(f"Upload directory: {upload_dir}")
        print(f"Profile pics directory: {profile_pics_dir}")
        print(f"Upload dir exists: {os.path.exists(upload_dir)}")
        print(f"Profile pics dir exists: {os.path.exists(profile_pics_dir)}")
        
        # List files in profile_pics
        if os.path.exists(profile_pics_dir):
            profile_files = os.listdir(profile_pics_dir)
            print(f"\nFiles in profile_pics: {profile_files}")
            
            # Test each profile image
            for filename in profile_files:
                file_path = os.path.join(profile_pics_dir, filename)
                print(f"\n--- Testing {filename} ---")
                print(f"File path: {file_path}")
                print(f"File exists: {os.path.exists(file_path)}")
                print(f"File size: {os.path.getsize(file_path) if os.path.exists(file_path) else 'N/A'} bytes")
                
                # Test if it's a valid image by checking file header
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(10)
                        print(f"File header: {header.hex()}")
                        
                        # Check common image signatures
                        if header.startswith(b'\xFF\xD8\xFF'):
                            print("✓ JPEG image detected")
                        elif header.startswith(b'\x89PNG'):
                            print("✓ PNG image detected")
                        elif header.startswith(b'GIF'):
                            print("✓ GIF image detected")
                        else:
                            print("✗ Unknown or invalid image format")
                except Exception as e:
                    print(f"✗ Error reading file: {e}")
        
        # Check main upload directory for old profile pics
        if os.path.exists(upload_dir):
            all_files = os.listdir(upload_dir)
            image_files = [f for f in all_files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')) and os.path.isfile(os.path.join(upload_dir, f))]
            print(f"\nImage files in main upload directory: {image_files}")
            
            for filename in image_files:
                file_path = os.path.join(upload_dir, filename)
                print(f"\n--- Testing {filename} (main upload dir) ---")
                print(f"File size: {os.path.getsize(file_path)} bytes")
                
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(10)
                        if header.startswith(b'\xFF\xD8\xFF'):
                            print("✓ JPEG image")
                        elif header.startswith(b'\x89PNG'):
                            print("✓ PNG image")
                        else:
                            print("✗ Invalid image format")
                except Exception as e:
                    print(f"✗ Error: {e}")
        
        # Test default avatar
        default_avatar = os.path.join(app.root_path, 'static', 'img', 'default-avatar.png')
        print(f"\n--- Testing Default Avatar ---")
        print(f"Default avatar path: {default_avatar}")
        print(f"Exists: {os.path.exists(default_avatar)}")
        if os.path.exists(default_avatar):
            print(f"Size: {os.path.getsize(default_avatar)} bytes")

if __name__ == "__main__":
    test_profile_images()
