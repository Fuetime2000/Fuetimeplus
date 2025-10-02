from app import app, db
from models.job_posting import JobPosting

def create_tables():
    with app.app_context():
        try:
            # This will create the JobPosting table if it doesn't exist
            JobPosting.__table__.create(db.engine)
            print("JobPosting table created successfully!")
        except Exception as e:
            print(f"Error creating JobPosting table: {str(e)}")

if __name__ == "__main__":
    create_tables()
