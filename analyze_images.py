#!/usr/bin/env python3
import os
import struct

def analyze_image_file(file_path):
    """Analyze an image file to determine its actual format"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(20)
            
        print(f"File: {os.path.basename(file_path)}")
        print(f"Size: {os.path.getsize(file_path)} bytes")
        print(f"Header (hex): {header[:20].hex()}")
        print(f"Header (ascii): {header[:20]}")
        
        # Check image signatures
        if header.startswith(b'\xFF\xD8\xFF'):
            return "JPEG"
        elif header.startswith(b'\x89PNG\r\n\x1a\n'):
            return "PNG"
        elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
            return "GIF"
        elif header.startswith(b'RIFF') and header[8:12] == b'WEBP':
            return "WebP"
        elif header.startswith(b'BM'):
            return "BMP"
        else:
            return "Unknown format"
            
    except Exception as e:
        return f"Error: {e}"

def check_problematic_images():
    """Check images that might be causing the Flutter error"""
    
    upload_dir = r"C:\Users\Admin\Fuetimeplus\static\uploads"
    profile_pics_dir = os.path.join(upload_dir, 'profile_pics')
    
    print("=== Analyzing Profile Images ===\n")
    
    # Check profile_pics directory
    if os.path.exists(profile_pics_dir):
        for filename in os.listdir(profile_pics_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                file_path = os.path.join(profile_pics_dir, filename)
                format_detected = analyze_image_file(file_path)
                print(f"Detected format: {format_detected}")
                
                # Check if extension matches actual format
                extension = os.path.splitext(filename)[1].lower()
                if format_detected == "JPEG" and extension not in ['.jpg', '.jpeg']:
                    print(f"⚠️  WARNING: JPEG file with {extension} extension")
                elif format_detected == "PNG" and extension != '.png':
                    print(f"⚠️  WARNING: PNG file with {extension} extension")
                print()
    
    # Check main upload directory
    print("=== Analyzing Upload Directory Images ===\n")
    for filename in os.listdir(upload_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                format_detected = analyze_image_file(file_path)
                print(f"Detected format: {format_detected}")
                
                # Check if extension matches actual format
                extension = os.path.splitext(filename)[1].lower()
                if format_detected == "JPEG" and extension not in ['.jpg', '.jpeg']:
                    print(f"⚠️  WARNING: JPEG file with {extension} extension")
                elif format_detected == "PNG" and extension != '.png':
                    print(f"⚠️  WARNING: PNG file with {extension} extension")
                print()

if __name__ == "__main__":
    check_problematic_images()
