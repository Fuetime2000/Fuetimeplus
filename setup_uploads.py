import os

def setup_upload_dirs():
    """Create necessary upload directories with proper permissions."""
    # Define the base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the directories we need to create
    dirs_to_create = [
        os.path.join(base_dir, 'static', 'uploads'),
        os.path.join(base_dir, 'static', 'uploads', 'profile_photos'),
        os.path.join(base_dir, 'static', 'uploads', 'profile_pics')
    ]
    
    # Create each directory if it doesn't exist
    for directory in dirs_to_create:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
            
            # List directory contents (for debugging)
            print(f"Contents of {directory}:")
            try:
                print(os.listdir(directory))
            except Exception as e:
                print(f"  Could not list directory: {e}")
                
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")

if __name__ == "__main__":
    print("Setting up upload directories...")
    setup_upload_dirs()
    print("Setup complete.")
    
    # Show the current working directory and absolute paths for reference
    print(f"\nCurrent working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    print("\nDirectory structure should now be:")
    print("- static/")
    print("  - uploads/")
    print("    - profile_photos/")
    print("    - profile_pics/")
