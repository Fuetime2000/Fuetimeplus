import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    # Application metadata
    APP_NAME = 'Fuetime'
    APP_VERSION = '1.0.0'
    APP_DESCRIPTION = 'A platform connecting clients with skilled professionals'
    APP_AUTHOR = 'Fuetime Team'
    APP_WEBSITE = 'https://fuetime.com'
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'dev-salt-change-in-production'
    
    # Database Configuration
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # Get database URL from environment variable or use SQLite as default
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            # Handle PostgreSQL URL format if needed
            if db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)
            return db_url
        # Default to SQLite for development
        return 'sqlite:///' + os.path.abspath(os.path.join(os.path.dirname(__file__), 'fuetime.db'))
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self):
        # Different engine options for SQLite and PostgreSQL
        if os.environ.get('DATABASE_URL'):
            # PostgreSQL settings for production
            return {
                'pool_pre_ping': True,
                'pool_recycle': 300,
                'pool_size': 30,
                'max_overflow': 40,
                'pool_timeout': 30,
                'connect_args': {'connect_timeout': 10}
            }
        # SQLite settings for development
        return {
            'connect_args': {'timeout': 15, 'check_same_thread': False}
        }
    
    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Security Headers
    SECURE_CONTENT_SECURITY_POLICY = {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", "https://*.razorpay.com"],
        'style-src': ["'self'", "'unsafe-inline'"],
        'img-src': ["'self'", "data:", "https: http:"],
        'font-src': ["'self'", "https: data:"],
        'connect-src': ["'self'"],
    }
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    
    # Caching
    CACHE_TYPE = 'SimpleCache'  # Use 'RedisCache' or 'MemcachedCache' in production
    CACHE_DEFAULT_TIMEOUT = 300
    
    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    PROFILE_PICS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads/profile_pics')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@fuetime.example.com')
    
    # Razorpay
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
    
    # Frontend URL for password reset links
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5000')
    
    # Rate limiting
    RATELIMIT_DEFAULT = '200 per day;50 per hour'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'logs/fuetime.log'




class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    LOG_LEVEL = 'WARNING'
    
    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self):
        # PostgreSQL optimized settings for production
        return {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_size': 30,
            'max_overflow': 40,
            'pool_timeout': 30,
            'connect_args': {'connect_timeout': 10}
        }


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_RECORD_QUERIES = True
    EXPLAIN_TEMPLATE_LOADING = False
    TEMPLATES_AUTO_RELOAD = True
    SESSION_COOKIE_SECURE = False
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'NullCache'


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_CHECK_DEFAULT = False
    RATELIMIT_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Set the default configuration
app_config = config[os.environ.get('FLASK_ENV', 'development').lower()]
