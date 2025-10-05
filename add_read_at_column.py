from app import app, db
from models.message import Message

def add_read_at_column():
    with app.app_context():
        # Check if the column exists
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('messages')]
        
        if 'read_at' not in columns:
            print("Adding read_at column to messages table...")
            # Use raw SQL to add the column
            with db.engine.connect() as connection:
                connection.execute('ALTER TABLE messages ADD COLUMN read_at DATETIME')
                connection.commit()
            print("Column added successfully!")
        else:
            print("read_at column already exists in messages table")

if __name__ == "__main__":
    add_read_at_column()
