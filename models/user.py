from datetime import datetime, timedelta
from models.base import Base, db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask import current_app
from time import time

class User(Base, UserMixin):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(20), nullable=False, default='worker')  # 'worker' or 'client'
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)
    full_name = db.Column(db.String(100), nullable=False)
    mother_name = db.Column(db.String(100))
    father_name = db.Column(db.String(100))
    live_location = db.Column(db.String(200))
    current_location = db.Column(db.String(200))
    work = db.Column(db.String(100))
    experience = db.Column(db.String(50))
    education = db.Column(db.String(200))
    profession = db.Column(db.String(100))  # User's profession/occupation
    work_experience = db.Column(db.String(500))  # Stores companies worked at (comma-separated)
    date_of_birth = db.Column(db.Date, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    photo = db.Column(db.String(200))
    bio = db.Column(db.Text)
    payment_type = db.Column(db.String(20))
    payment_charge = db.Column(db.Float)
    skills = db.Column(db.String(500))
    categories = db.Column(db.String(200))
    availability = db.Column(db.String(20), default="available")
    average_rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    is_online = db.Column(db.Boolean, default=False)
    profile_views = db.Column(db.Integer, default=0)
    wallet_balance = db.Column(db.Float, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    active = db.Column(db.Boolean, default=True)
    authenticated = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)
    blocked = db.Column(db.Boolean, default=False)
    verified = db.Column(db.Boolean, default=False, nullable=False, server_default='0')
    email_otp = db.Column(db.String(6))
    phone_otp = db.Column(db.String(6))
    otp_expiry = db.Column(db.DateTime, nullable=True)  # When the OTP will expire
    email_notifications = db.Column(db.Boolean, default=True)
    message_notifications = db.Column(db.Boolean, default=True)
    review_notifications = db.Column(db.Boolean, default=True)
    
    # Relationships
    # Portfolio relationships
    portfolios = db.relationship('Portfolio', back_populates='user', lazy=True)
    portfolio_projects = db.relationship('PortfolioProject', back_populates='user', lazy='dynamic')
    projects = db.relationship('Project', back_populates='user', lazy='dynamic')
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', back_populates='sender', lazy='dynamic')
    messages_received = db.relationship('Message', foreign_keys='Message.receiver_id', back_populates='receiver', lazy='dynamic')
    # Contact request relationships (backrefs are defined in ContactRequest model):
    # - contact_requests_sent: contact requests sent by this user
    # - contact_requests_received: contact requests received by this user
    transactions = db.relationship('Transaction', back_populates='user', lazy='dynamic')
    reviews_given = db.relationship('Review', foreign_keys='Review.reviewer_id', back_populates='reviewer', lazy='dynamic')
    reviews_received = db.relationship('Review', foreign_keys='Review.worker_id', back_populates='worker', lazy='dynamic')
    # Call relationships (backrefs are defined in Call model):
    # - outgoing_calls: calls made by this user (caller)
    # - incoming_calls: calls received by this user (callee)
    # Report relationships (backrefs are defined in Report model):
    # - reports_made: reports submitted by this user
    # - reports_received: reports filed against this user
    # Saved users relationships (backrefs are defined in SavedUser model):
    # - saved_users: users saved by this user
    # - saved_by_users: users who saved this user
    
    # Job posting relationships (backrefs are defined in JobPosting model):
    # - job_postings: jobs posted by this user (client)
    # - assigned_jobs: jobs assigned to this user (worker)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        return True
        
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)
    
    def is_active(self):
        return self.active
        
    def get_profile_pic_url(self):
        """
        Returns the URL for the user's profile picture.
        If no profile picture is set, returns a default avatar URL.
        """
        if self.photo:
            # Check if the photo is already a full URL
            if self.photo.startswith(('http://', 'https://')):
                return self.photo
            
            # For local photos, check if file exists before returning URL
            import os
            from flask import current_app
            
            # First check profile_pics subdirectory
            photo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pics', self.photo)
            if os.path.exists(photo_path):
                return f"/profile_pic/{self.photo}"
            
            # Then check main uploads directory for backward compatibility
            photo_path_main = os.path.join(current_app.root_path, 'static', 'uploads', self.photo)
            if os.path.exists(photo_path_main):
                return f"/profile_pic/{self.photo}"
        
        # Return a default avatar URL if no photo is set or file doesn't exist
        return "/static/img/default-avatar.png"
    
    @property
    def is_authenticated(self):
        return self.authenticated and self.active
    
    def is_anonymous(self):
        return False
    
    def update_rating(self):
        reviews = self.reviews_received.all()
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            self.average_rating = total_rating / len(reviews)
            self.total_reviews = len(reviews)
        else:
            self.average_rating = 0.0
            self.total_reviews = 0
    
    def update_last_seen(self):
        self.last_active = datetime.utcnow()
    
    def get_unread_messages_count(self):
        from models.message import Message
        return Message.query.filter_by(receiver_id=self.id, is_read=False).count()
        
    def get_auth_token(self, expires_in=3600):
        """Generate a JWT token for API authentication"""
        return jwt.encode(
            {'user_id': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    def get_related_users(self, limit=6):
        """Find worker users with similar skills and location"""
        from models.user import User
        
        # Start with all active worker users except current user
        base_query = User.query.filter(
            User.id != self.id,
            User.active == True,
            User.user_type == 'worker',  # Only include worker users
            User.is_admin == False  # Exclude admin users
        )
        
        # First try to find users with similar skills and location
        if self.skills or self.current_location:
            conditions = []
            
            # Add skill conditions if available
            if self.skills:
                skills_list = [skill.strip().lower() for skill in self.skills.split(',') if skill.strip()]
                if skills_list:
                    skill_conditions = [User.skills.ilike(f'%{skill}%') for skill in skills_list]
                    conditions.append(db.or_(*skill_conditions))
            
            # Add location conditions if available
            if self.current_location:
                location_conditions = [
                    User.current_location.ilike(f'%{self.current_location}%'),
                    User.live_location.ilike(f'%{self.current_location}%')
                ]
                conditions.append(db.or_(*location_conditions))
            
            # Apply all conditions with OR between them if we have any
            if conditions:
                query = base_query.filter(db.or_(*conditions))
            else:
                query = base_query
        else:
            query = base_query
        
        # Get initial results with priority to those with higher ratings and more reviews
        results = query.order_by(
            User.average_rating.desc(),
            User.total_reviews.desc(),
            User.created_at.desc()  # Newer users as tiebreaker
        ).limit(limit * 2).all()
        
        # If we still don't have enough results, get any active worker users
        if len(results) < limit:
            more_users = User.query.filter(
                User.id != self.id,
                User.active == True,
                User.user_type == 'worker',
                User.is_admin == False,
                ~User.id.in_([u.id for u in results] if results else [])
            ).order_by(
                User.average_rating.desc(),
                User.total_reviews.desc(),
                User.created_at.desc()
            ).limit(limit - len(results)).all()
            results.extend(more_users)
        
        # Log the number of results for debugging
        from flask import current_app
        current_app.logger.info(f"Found {len(results)} related users for user {self.id}")
        
        # Return up to the requested limit
        return results[:limit]

    def generate_auth_token(self, expires_in=3600):
        """Generate a JWT token for API authentication"""
        payload = {
            'user_id': self.id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
            'sub': str(self.id)
        }
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_auth_token(token):
        """Verify JWT token and return user if valid"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            return User.query.get(payload['user_id'])
        except jwt.ExpiredSignatureError:
            return None  # Token expired
        except (jwt.InvalidTokenError, jwt.DecodeError):
            return None  # Invalid token

    def to_dict(self):
        """Convert user object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'user_type': self.user_type,
            'phone': self.phone,
            'is_verified': self.email_verified,
            'wallet_balance': float(self.wallet_balance) if self.wallet_balance else 0.0,
            'profile_picture': self.photo,
            'is_online': self.is_online,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.active
        }

    def __repr__(self):
        return f'<User {self.username}>'
