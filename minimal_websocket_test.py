#!/usr/bin/env python3
"""
Minimal WebSocket test for Windows compatibility
"""
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, UserMixin

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'

# Initialize SocketIO with threading mode (Windows compatible)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    engineio_logger=False,
    logger=False,
    manage_session=False
)

# Simple login manager setup
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Basic WebSocket handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected to default namespace')
    return True

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from default namespace')

@socketio.on('connect', namespace='/ws/user')
def handle_user_connect():
    print('Client connected to /ws/user namespace')
    return True

@socketio.on('disconnect', namespace='/ws/user')
def handle_user_disconnect():
    print('Client disconnected from /ws/user namespace')

if __name__ == '__main__':
    print("Starting minimal WebSocket test server with threading...")
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )
