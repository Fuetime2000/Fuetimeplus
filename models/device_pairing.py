from extensions import db
from datetime import datetime

class DevicePairing(db.Model):
    """Model for storing device pairing relationships for emergency alerts"""
    __tablename__ = 'device_pairings'
    
    id = db.Column(db.Integer, primary_key=True)
    pairing_code = db.Column(db.String(6), unique=True, nullable=False, index=True)
    device_a_token = db.Column(db.String(255), nullable=False, index=True)
    device_b_token = db.Column(db.String(255), nullable=True, index=True)
    device_a_name = db.Column(db.String(100))
    device_b_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    paired_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'pairing_code': self.pairing_code,
            'device_a_token': self.device_a_token,
            'device_b_token': self.device_b_token,
            'device_a_name': self.device_a_name,
            'device_b_name': self.device_b_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'paired_at': self.paired_at.isoformat() if self.paired_at else None
        }


class EmergencyAlert(db.Model):
    """Model for logging emergency alerts"""
    __tablename__ = 'emergency_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    from_device_token = db.Column(db.String(255), nullable=False, index=True)
    to_device_token = db.Column(db.String(255), nullable=False, index=True)
    reason = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Numeric(10, 8), nullable=True)
    longitude = db.Column(db.Numeric(11, 8), nullable=True)
    accuracy = db.Column(db.Float, nullable=True)
    battery_level = db.Column(db.Integer, nullable=True)
    message = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.BigInteger, nullable=False, index=True)
    delivered = db.Column(db.Boolean, default=False)
    delivered_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'from_device_token': self.from_device_token,
            'to_device_token': self.to_device_token,
            'reason': self.reason,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'accuracy': self.accuracy,
            'battery_level': self.battery_level,
            'message': self.message,
            'timestamp': self.timestamp,
            'delivered': self.delivered,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
