from app import app, db
from models.job_posting import JobPosting

def create_job_postings_table():
    with app.app_context():
        try:
            # Create all tables that don't exist yet
            db.create_all()
            print("Job postings table created successfully!")
            
            # Verify the table was created
            with db.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='job_postings'
                """))
                if result.fetchone():
                    print("Verified: job_postings table exists in the database.")
                else:
                    print("Warning: job_postings table was not created.")
                    
        except Exception as e:
            print(f"Error creating job postings table: {str(e)}")
            raise

if __name__ == "__main__":
    create_job_postings_table()
