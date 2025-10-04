from datetime import datetime
from models.base import Base, db

class Message(Base):
    __tablename__ = 'messages'
    __module__ = 'models.message'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text)
    attachment = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships with lazy loading for better performance
    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='messages_sent')
    receiver = db.relationship('User', foreign_keys=[receiver_id], back_populates='messages_received')
    
    def __repr__(self):
        return f'<Message {self.id} from User {self.sender_id} to User {self.receiver_id}>'
