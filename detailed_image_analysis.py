#!/usr/bin/env python3
import os
from PIL import Image

def detailed_image_check(file_path):
    """Detailed image analysis with specific error messages"""
    try:
        # Try to open the file
        with open(file_path, 'rb') as f:
            header = f.read(100)
        
        print(f"File: {os.path.basename(file_path)}")
        print(f"Size: {os.path.getsize(file_path)} bytes")
        print(f"First 50 bytes (hex): {header[:50].hex()}")
        
        # Try PIL
        try:
            with Image.open(file_path) as img:
                print(f"✓ PIL can open: {img.format} {img.size} {img.mode}")
                img.verify()
                print("✓ PIL verify passed")
                
                # Try loading
                with Image.open(file_path) as img:
                    img.load()
                print("✓ PIL load passed")
                
        except Exception as pil_error:
            print(f"❌ PIL Error: {pil_error}")
            
            # Try to identify the issue
            error_str = str(pil_error).lower()
            if "truncated" in error_str:
                return "Image file is truncated/corrupted"
            elif "cannot identify" in error_str:
                return "Cannot identify image file format"
            elif "bad" in error_str and "data" in error_str:
                return "Bad image data"
            elif "premature" in error_str:
                return "Premature end of image file"
            else:
                return f"PIL error: {pil_error}"
                
    except Exception as e:
        return f"File error: {e}"
    
    return "Valid image"

def analyze_all_images():
    """Analyze all images with detailed error reporting"""
    
    upload_dir = r"C:\Users\Admin\Fuetimeplus\static\uploads"
    profile_pics_dir = os.path.join(upload_dir, 'profile_pics')
    
    print("=== Detailed Image Analysis ===\n")
    
    issues_found = []
    
    for directory in [profile_pics_dir, upload_dir]:
        if not os.path.exists(directory):
            continue
            
        for filename in os.listdir(directory):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
                file_path = os.path.join(directory, filename)
                
                if os.path.isfile(file_path):
                    print(f"\n--- {filename} ---")
                    issue = detailed_image_check(file_path)
                    
                    if issue != "Valid image":
                        issues_found.append((filename, issue))
                        print(f"❌ ISSUE: {issue}")
                    else:
                        print("✅ OK")
    
    print(f"\n=== Issues Summary ===")
    if issues_found:
        print(f"Found {len(issues_found)} problematic images:")
        for filename, issue in issues_found:
            print(f"  • {filename}: {issue}")
            
        print(f"\n=== Recommendations ===")
        print("1. All images appear to be corrupted")
        print("2. This explains the Flutter 'Invalid image data' error")
        print("3. Users need to re-upload their profile pictures")
        print("4. Consider adding image validation during upload")
        
    else:
        print("No issues found")

if __name__ == "__main__":
    analyze_all_images()
