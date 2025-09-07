import os

def check_file(filepath):
    print(f"Checking file: {os.path.abspath(filepath)}")
    
    try:
        # Check if file exists
        exists = os.path.isfile(filepath)
        print(f"File exists: {exists}")
        
        if exists:
            # Get file size
            size = os.path.getsize(filepath)
            print(f"File size: {size} bytes")
            
            # Try to read first few bytes
            try:
                with open(filepath, 'rb') as f:
                    header = f.read(16)
                    print(f"First 16 bytes: {header}")
            except Exception as e:
                print(f"Error reading file: {e}")
        
        return exists
    except Exception as e:
        print(f"Error checking file: {e}")
        return False

if __name__ == "__main__":
    db_path = 'fuetime.db'
    if not check_file(db_path):
        print("\nDatabase file check failed.")
        exit(1)
    else:
        print("\nDatabase file check completed.")
        exit(0)
