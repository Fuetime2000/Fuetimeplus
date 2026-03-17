import sys

# Apply monkey patching before any other imports
import sys
import platform

# Use threading mode on Windows for better compatibility
if platform.system() == 'Windows':
    print("Using threading mode for SocketIO on Windows")
    async_mode = 'threading'
else:
    try:
        import eventlet
        eventlet.monkey_patch()
        print("Using eventlet for SocketIO")
        async_mode = 'eventlet'
    except ImportError:
        try:
            from gevent import monkey
            monkey.patch_all()
            print("Using gevent for SocketIO")
            async_mode = 'gevent'
        except ImportError:
            print("Warning: eventlet/gevent not available. Using threading mode")
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

# Initialize SocketIO with WebSocket support
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode=async_mode,
    engineio_logger=True,  # Enable logging for debugging
    logger=True,  # Enable logging for debugging
    ping_timeout=60,
    ping_interval=25,
    manage_session=False,  # Let Flask manage sessions
    socketio_path='socket.io',
    always_connect=True,  # Ensure connections are established
    transports=['polling', 'websocket'],  # Enable both transports
    allow_upgrades=True,  # Allow upgrades from polling to websocket
    upgrade_timeout=10,  # Set upgrade timeout
    websocket_timeout=5,  # WebSocket timeout
    http_compression=True,  # Enable compression
    compression_level=3  # Compression level
)

# Initialize CSRF protection
csrf = CSRFProtect()

# Initialize Flask-Mail
mail = Mail()
