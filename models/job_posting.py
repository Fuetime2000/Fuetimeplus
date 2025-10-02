import json
from datetime import datetime
from extensions import db
from sqlalchemy import ForeignKey, text, TypeDecorator, Text
from sqlalchemy.orm import relationship
from sqlalchemy.schema import CreateTable

# Custom JSON type for SQLite
class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.
    Usage::
        JSONEncodedDict()
    """
    impl = Text
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value if value is not None else {}

# Use JSON for SQLite, JSONB for PostgreSQL
JSONType = JSONEncodedDict

class JobPosting(db.Model):
    """Model for job postings by clients looking for workers"""
    __tablename__ = 'job_postings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)  # e.g., 'web_development', 'plumbing', etc.
    budget = db.Column(db.Numeric(10, 2), nullable=False)
    budget_type = db.Column(db.String(20), nullable=False)  # 'fixed' or 'hourly'
    location = db.Column(db.String(200))
    address = db.Column(db.String(500))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    images = db.Column(JSONType)  # Store image paths as JSON array
    status = db.Column(db.String(20), default='open')  # 'open', 'in_progress', 'completed', 'cancelled'
    client_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    worker_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=True)  # Assigned worker
    duration = db.Column(db.String(100))  # e.g., '1 week', '1 month', 'Ongoing'
    skills_required = db.Column(JSONType)  # Array of required skills
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships with explicit table name for User
    client = relationship('User', 
                         foreign_keys=[client_id], 
                         backref=db.backref('job_postings', lazy='dynamic'),
                         primaryjoin='User.id==JobPosting.client_id')
    worker = relationship('User', 
                         foreign_keys=[worker_id], 
                         backref=db.backref('assigned_jobs', lazy='dynamic'),
                         primaryjoin='User.id==JobPosting.worker_id')
    
    @classmethod
    def create_table(cls, engine):
        """Create the table directly using SQL"""
        sql = """
        CREATE TABLE IF NOT EXISTS public.job_postings (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            category VARCHAR(100) NOT NULL,
            budget NUMERIC(10, 2) NOT NULL,
            budget_type VARCHAR(20) NOT NULL,
            location VARCHAR(200),
            address VARCHAR(500),
            latitude FLOAT,
            longitude FLOAT,
            images JSONB,
            status VARCHAR(20) DEFAULT 'open' NOT NULL,
            client_id INTEGER NOT NULL REFERENCES public.user(id),
            worker_id INTEGER REFERENCES public.user(id),
            duration VARCHAR(100),
            skills_required JSONB,
            contact_phone VARCHAR(20),
            contact_email VARCHAR(120),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_job_postings_category ON public.job_postings(category);
        CREATE INDEX IF NOT EXISTS idx_job_postings_status ON public.job_postings(status);
        CREATE INDEX IF NOT EXISTS idx_job_postings_client_id ON public.job_postings(client_id);
        CREATE INDEX IF NOT EXISTS idx_job_postings_worker_id ON public.job_postings(worker_id);
        """
        
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
    
    def to_dict(self):
        """Convert job posting to dictionary for JSON response"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'budget': float(self.budget) if self.budget else None,
            'budget_type': self.budget_type,
            'location': self.location,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'images': self.images or [],
            'status': self.status,
            'client_id': self.client_id,
            'worker_id': self.worker_id,
            'duration': self.duration,
            'skills_required': self.skills_required or [],
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'client_name': self.client.full_name if self.client else None,
            'client_avatar': self.client.get_profile_pic_url() if self.client else None
        }
    
    def __repr__(self):
        return f'<JobPosting {self.title} - {self.status}>'
