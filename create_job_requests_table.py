from app import app, db
from models.job_request import JobRequest

def create_tables():
    with app.app_context():
        try:
            # This will create the JobRequest table if it doesn't exist
            JobRequest.__table__.create(db.engine)
            print("JobRequest table created successfully!")
        except Exception as e:
            print(f"Error creating JobRequest table: {str(e)}")

if __name__ == "__main__":
    create_tables()
