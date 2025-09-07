import os
import sys
import stat

def check_file_access(filepath):
    print(f"Checking access to: {os.path.abspath(filepath)}")
    
    # Check if file exists
    if not os.path.exists(filepath):
        print("Error: File does not exist.")
        return False
    
    # Get file stats
    try:
        file_stat = os.stat(filepath)
        print(f"File size: {file_stat.st_size} bytes")
        print(f"Last modified: {file_stat.st_mtime}")
        
        # Check permissions
        print("\nPermissions:")
        print(f"- Readable: {os.access(filepath, os.R_OK)}")
        print(f"- Writable: {os.access(filepath, os.W_OK)}")
        print(f"- Executable: {os.access(filepath, os.X_OK)}")
        
        # Try to open the file
        try:
            with open(filepath, 'rb') as f:
                header = f.read(16)
                print(f"\nFirst 16 bytes: {header}")
                return True
        except Exception as e:
            print(f"\nError reading file: {e}")
            return False
            
    except Exception as e:
        print(f"Error getting file stats: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = 'fuetime.db'
    
    if not check_file_access(filepath):
        print("\nFile access check failed.")
        sys.exit(1)
    else:
        print("\nFile access check passed.")
        sys.exit(0)
