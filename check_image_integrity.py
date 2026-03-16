#!/usr/bin/env python3
import os
import struct
from PIL import Image

def check_image_integrity(file_path):
    """Check if an image file is valid and can be opened"""
    try:
        # Try to open with PIL
        with Image.open(file_path) as img:
            img.verify()  # Verify the image data
            img.load()    # Load the image data to ensure it's valid
        return True, "Valid image"
    except Exception as e:
        return False, f"Invalid image: {str(e)}"

def find_corrupted_images():
    """Find all image files and check for corruption"""
    
    upload_dir = r"C:\Users\Admin\Fuetimeplus\static\uploads"
    profile_pics_dir = os.path.join(upload_dir, 'profile_pics')
    
    print("=== Checking Image Integrity ===\n")
    
    problematic_files = []
    
    # Check all image files
    for directory in [profile_pics_dir, upload_dir]:
        if not os.path.exists(directory):
            continue
            
        print(f"Checking directory: {directory}")
        
        for filename in os.listdir(directory):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
                file_path = os.path.join(directory, filename)
                
                if os.path.isfile(file_path):
                    # Check file size
                    file_size = os.path.getsize(file_path)
                    
                    # Check for zero-byte files
                    if file_size == 0:
                        print(f"❌ ZERO-BYTE FILE: {filename}")
                        problematic_files.append((filename, "Zero-byte file"))
                        continue
                    
                    # Check image integrity
                    is_valid, message = check_image_integrity(file_path)
                    
                    if is_valid:
                        print(f"✅ {filename} - {file_size} bytes - Valid")
                    else:
                        print(f"❌ {filename} - {file_size} bytes - {message}")
                        problematic_files.append((filename, message))
    
    print(f"\n=== Summary ===")
    if problematic_files:
        print(f"Found {len(problematic_files)} problematic files:")
        for filename, issue in problematic_files:
            print(f"  - {filename}: {issue}")
    else:
        print("All images are valid!")
    
    return problematic_files

if __name__ == "__main__":
    find_corrupted_images()
