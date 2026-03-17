"""
Base model for all database models
"""
from flask_sqlalchemy import SQLAlchemy

# Create db instance here to avoid circular imports
db = SQLAlchemy()

class Base(db.Model):
    __abstract__ = True
