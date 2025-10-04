from datetime import datetime
from extensions import db
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import relationship

class JobRequest(db.Model):
    """Model for job applications/requests from workers to job postings"""
    __tablename__ = 'job_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, ForeignKey('job_postings.id'), nullable=False)
    worker_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, accepted, rejected, cancelled
    message = db.Column(db.Text)
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship('JobPosting', backref=db.backref('requests', lazy='dynamic'))
    worker = relationship('User', foreign_keys=[worker_id], backref=db.backref('job_applications', lazy='dynamic'))
    client = relationship('User', foreign_keys=[client_id], backref=db.backref('received_job_requests', lazy='dynamic'))
    
    def to_dict(self):
        """Convert job request to dictionary"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'worker_id': self.worker_id,
            'client_id': self.client_id,
            'status': self.status,
            'message': self.message,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_table(cls, engine):
        """Create the table directly using SQL"""
        sql = """
        CREATE TABLE IF NOT EXISTS job_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'pending' NOT NULL,
            message TEXT,
            rejection_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES job_postings (id) ON DELETE CASCADE,
            FOREIGN KEY (worker_id) REFERENCES user (id) ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES user (id) ON DELETE CASCADE,
            UNIQUE(job_id, worker_id)  -- A worker can only apply once per job
        );
        
        CREATE INDEX IF NOT EXISTS idx_job_requests_job_id ON job_requests(job_id);
        CREATE INDEX IF NOT EXISTS idx_job_requests_worker_id ON job_requests(worker_id);
        CREATE INDEX IF NOT EXISTS idx_job_requests_client_id ON job_requests(client_id);
        CREATE INDEX IF NOT EXISTS idx_job_requests_status ON job_requests(status);
        """
        
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
