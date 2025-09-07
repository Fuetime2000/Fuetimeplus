from datetime import datetime
from models.base import Base, db

class SavedUser(Base):
    __tablename__ = 'saved_user'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # User who saved
    saved_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # User being saved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add unique constraint to prevent duplicate saves
    __table_args__ = (db.UniqueConstraint('user_id', 'saved_user_id', name='unique_user_save'),)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='saved_users')
    saved_user = db.relationship('User', foreign_keys=[saved_user_id], backref='saved_by_users')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'saved_user_id': self.saved_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<SavedUser {self.user_id} -> {self.saved_user_id}>'
