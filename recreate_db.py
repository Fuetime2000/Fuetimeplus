from app import app
from extensions import db
from models.user import User
from models.message import Message
from models.job_posting import JobPosting
from models.job_request import JobRequest

# Initialize the app with the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fuetime.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    
    print("Creating all tables...")
    db.create_all()
    
    print("Database recreated successfully!")
