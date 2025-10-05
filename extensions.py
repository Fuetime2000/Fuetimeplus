import sys

# Apply monkey patching before any other imports
try:
    from gevent import monkey
    monkey.patch_all()
    print("Using gevent for SocketIO")
    async_mode = 'gevent'
except ImportError:
    print("Warning: gevent is not available. Using threading mode")
    async_mode = 'threading'

# Now import other modules after monkey patching
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_babel import Babel
from flask_caching import Cache
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
babel = Babel()
cache = Cache()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize SocketIO
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode=async_mode,
    engineio_logger=True,
    logger=True,
    ping_timeout=60,
    manage_session=False  # Let Flask handle the session
)

# Initialize CSRF protection
csrf = CSRFProtect()

# Initialize Flask-Mail
mail = Mail()
