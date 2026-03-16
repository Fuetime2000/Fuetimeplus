#!/usr/bin/env python3
import requests
import os
from app import app

def test_image_serving():
    """Test how the Flask app serves images with HTTP headers"""
    
    with app.test_client() as client:
        print("=== Testing Image Serving HTTP Headers ===\n")
        
        # Test URLs to check
        test_urls = [
            '/profile_pic/c886e5c3-7052-4a9f-8773-d5a900527f9e.jpg',
            '/profile_pic/20251209_224222_IMG-251209-183407-35767.jpg',
            '/profile_pic/20260209_234740_IMG_20260131_174057.jpg',
            '/profile_pic/nonexistent.jpg',  # Should return default avatar
        ]
        
        for url in test_urls:
            print(f"--- Testing {url} ---")
            
            response = client.get(url)
            
            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.content_type}")
            print(f"Content-Length: {len(response.data)} bytes")
            
            # Check if it's the default avatar
            if len(response.data) < 1000:  # Default avatar is very small
                print("⚠️  Returned default avatar (file not found or error)")
            else:
                print("✅ Returned image file")
            
            # Check content-type matches file extension
            if url.endswith('.jpg') and response.content_type != 'image/jpeg':
                print(f"⚠️  WARNING: .jpg file but Content-Type is {response.content_type}")
            elif url.endswith('.png') and response.content_type != 'image/png':
                print(f"⚠️  WARNING: .png file but Content-Type is {response.content_type}")
            
            print()

def check_file_extension_vs_content():
    """Check if file extensions match actual content"""
    
    upload_dir = r"C:\Users\Admin\Fuetimeplus\static\uploads"
    profile_pics_dir = os.path.join(upload_dir, 'profile_pics')
    
    print("=== File Extension vs Content Analysis ===\n")
    
    for directory in [profile_pics_dir, upload_dir]:
        if not os.path.exists(directory):
            continue
            
        for filename in os.listdir(directory):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                file_path = os.path.join(directory, filename)
                
                if os.path.isfile(file_path):
                    # Read file header to determine actual format
                    with open(file_path, 'rb') as f:
                        header = f.read(10)
                    
                    extension = os.path.splitext(filename)[1].lower()
                    
                    if header.startswith(b'\xFF\xD8\xFF'):
                        actual_format = 'JPEG'
                        expected_mime = 'image/jpeg'
                    elif header.startswith(b'\x89PNG'):
                        actual_format = 'PNG'
                        expected_mime = 'image/png'
                    elif header.startswith(b'GIF'):
                        actual_format = 'GIF'
                        expected_mime = 'image/gif'
                    else:
                        actual_format = 'Unknown'
                        expected_mime = 'application/octet-stream'
                    
                    print(f"File: {filename}")
                    print(f"  Extension: {extension}")
                    print(f"  Actual format: {actual_format}")
                    print(f"  Expected MIME: {expected_mime}")
                    
                    if (extension in ['.jpg', '.jpeg'] and actual_format != 'JPEG') or \
                       (extension == '.png' and actual_format != 'PNG') or \
                       (extension == '.gif' and actual_format != 'GIF'):
                        print(f"  ❌ MISMATCH: Extension doesn't match content!")
                        
                        # Suggest correct filename
                        base_name = os.path.splitext(filename)[0]
                        if actual_format == 'JPEG':
                            suggested = f"{base_name}.jpg"
                        elif actual_format == 'PNG':
                            suggested = f"{base_name}.png"
                        elif actual_format == 'GIF':
                            suggested = f"{base_name}.gif"
                        else:
                            suggested = filename
                        
                        print(f"  💡 Suggest renaming to: {suggested}")
                    else:
                        print(f"  ✅ Extension matches content")
                    print()

if __name__ == "__main__":
    check_file_extension_vs_content()
    test_image_serving()
