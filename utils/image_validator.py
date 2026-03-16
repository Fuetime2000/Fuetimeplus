#!/usr/bin/env python3
"""
Image validation utilities to prevent Flutter "Invalid image data" errors
"""

import os
try:
    import imghdr
except ImportError:
    imghdr = None
from PIL import Image
from werkzeug.utils import secure_filename

def validate_image_file(file_storage, allowed_extensions=None):
    """
    Comprehensive image validation to prevent Flutter compatibility issues
    
    Args:
        file_storage: Flask FileStorage object
        allowed_extensions: Set of allowed file extensions
        
    Returns:
        tuple: (is_valid, error_message, corrected_filename)
    """
    
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Check if file was actually uploaded
    if not file_storage or file_storage.filename == '':
        return False, "No file selected", None
    
    # Get original filename
    original_filename = file_storage.filename
    secure_name = secure_filename(original_filename)
    
    # Check file extension
    extension = os.path.splitext(secure_name)[1].lower().lstrip('.')
    if extension not in allowed_extensions:
        return False, f"File type .{extension} not allowed", None
    
    # Check file size (max 5MB)
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        return False, "File too large (max 5MB)", None
    
    if file_size == 0:
        return False, "File is empty", None
    
    # Read file content for validation
    file_content = file_storage.read()
    file_storage.seek(0)
    
    # Detect actual image format using multiple methods
    actual_format = None
    
    # Method 1: PIL detection
    try:
        with Image.open(file_storage) as img:
            pil_format = img.format.lower()
            img.verify()  # Verify image integrity
            file_storage.seek(0)
            actual_format = pil_format
    except Exception:
        file_storage.seek(0)
    
    # Method 2: imghdr detection (backup)
    if not actual_format and imghdr:
        try:
            detected_format = imghdr.what(None, file_content)
            if detected_format:
                actual_format = detected_format
        except Exception:
            pass
    
    # Method 3: Manual header detection (final backup)
    if not actual_format:
        if file_content.startswith(b'\xFF\xD8\xFF'):
            actual_format = 'jpeg'
        elif file_content.startswith(b'\x89PNG'):
            actual_format = 'png'
        elif file_content.startswith(b'GIF87a') or file_content.startswith(b'GIF89a'):
            actual_format = 'gif'
        else:
            return False, "Cannot identify image format", None
    
    # Normalize format names
    if actual_format == 'jpeg':
        actual_format = 'jpg'
    
    # Check if detected format matches file extension
    if actual_format != extension:
        # Auto-correct the filename extension
        base_name = os.path.splitext(secure_name)[0]
        corrected_filename = f"{base_name}.{actual_format}"
        
        return True, f"File format corrected from .{extension} to .{actual_format}", corrected_filename
    
    # Final validation - try to load the image completely
    try:
        with Image.open(file_storage) as img:
            img.load()  # Ensure image can be fully loaded
        file_storage.seek(0)
    except Exception as e:
        return False, f"Image file is corrupted: {str(e)}", None
    
    file_storage.seek(0)
    return True, "Valid image", secure_name

def fix_existing_images(upload_dir):
    """
    Scan and fix existing images with wrong extensions
    
    Args:
        upload_dir: Path to uploads directory
        
    Returns:
        list: List of fixed files
    """
    
    fixed_files = []
    
    for root, dirs, files in os.walk(upload_dir):
        for filename in files:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                file_path = os.path.join(root, filename)
                
                try:
                    # Detect actual format
                    with open(file_path, 'rb') as f:
                        header = f.read(10)
                    
                    # Determine actual format
                    if header.startswith(b'\xFF\xD8\xFF'):
                        actual_format = 'jpg'
                    elif header.startswith(b'\x89PNG'):
                        actual_format = 'png'
                    elif header.startswith(b'GIF'):
                        actual_format = 'gif'
                    else:
                        continue  # Skip unknown formats
                    
                    # Check if extension matches
                    extension = os.path.splitext(filename)[1].lower().lstrip('.')
                    
                    if actual_format != extension:
                        # Fix the filename
                        base_name = os.path.splitext(filename)[0]
                        new_filename = f"{base_name}.{actual_format}"
                        new_path = os.path.join(root, new_filename)
                        
                        # Rename the file
                        os.rename(file_path, new_path)
                        fixed_files.append((filename, new_filename))
                        
                        print(f"Fixed: {filename} → {new_filename}")
                
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
    
    return fixed_files

if __name__ == "__main__":
    # Test the function on existing images
    upload_dir = r"C:\Users\Admin\Fuetimeplus\static\uploads"
    print("=== Fixing Existing Images ===")
    fixed = fix_existing_images(upload_dir)
    
    if fixed:
        print(f"\nFixed {len(fixed)} files:")
        for old, new in fixed:
            print(f"  {old} → {new}")
    else:
        print("No files needed fixing")
