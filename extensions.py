import sys
import platform

# Force threading mode to avoid monkey patching issues with imports
print("Forcing threading mode for SocketIO to avoid import lock conflicts")
async_mode = 'threading'

# Import Flask extensions after setting async mode
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
# Note: db is imported from models.base to avoid circular imports
# Don't create db instance here - use the one from models.base
login_manager = LoginManager()
migrate = Migrate()
babel = Babel()
cache = Cache()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize SocketIO with threading mode for stability
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode=async_mode,
    engineio_logger=False,  # Disable logging for production
    logger=False,  # Disable logging for production
    ping_timeout=60,
    ping_interval=25,
    manage_session=False,  # Let Flask manage sessions
    socketio_path='socket.io',
    always_connect=True,  # Ensure connections are established
    transports=['polling'],  # Use only polling to avoid WebSocket issues
    allow_upgrades=False,  # Disable upgrades to prevent connection issues
    http_compression=True,  # Enable compression
    compression_level=3  # Compression level
)

# Initialize CSRF protection
csrf = CSRFProtect()

# Initialize Flask-Mail
mail = Mail()
