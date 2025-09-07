from app import create_app, db
from models.message import Message
import sys

def check_and_fix_read_at_column():
    app = create_app()
    with app.app_context():
        # Check if the column exists
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('messages')]
        
        if 'read_at' not in columns:
            print("Column 'read_at' is missing from 'messages' table. Adding it now...")
            try:
                # Add the column using raw SQL
                db.engine.execute('ALTER TABLE messages ADD COLUMN read_at DATETIME')
                db.session.commit()
                print("Successfully added 'read_at' column to 'messages' table.")
            except Exception as e:
                db.session.rollback()
                print(f"Error adding 'read_at' column: {str(e)}")
                return False
        else:
            print("'read_at' column already exists in 'messages' table.")
        
        return True

if __name__ == "__main__":
    if check_and_fix_read_at_column():
        sys.exit(0)
    else:
        sys.exit(1)
