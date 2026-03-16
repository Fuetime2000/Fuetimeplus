#!/usr/bin/env python3
"""
Test script to verify room-based messaging functionality
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

# Initialize SocketIO with threading mode
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

# Test handlers (copied from app.py)
@socketio.on('connect')
def handle_connect():
    print('Client connected to default namespace')
    return True

@socketio.on('connect', namespace='/ws/user')
def handle_user_connect():
    print('Client connected to /ws/user namespace')
    return True

@socketio.on('join_user_room', namespace='/ws/user')
def handle_join_user_room(user_id):
    """Handle explicit room joining request"""
    print(f"TEST: join_user_room called for user_id={user_id}")
    room_name = f'user_{user_id}'
    join_room(room_name)
    emit('room_joined', {'room': room_name})
    print(f"TEST: User {user_id} successfully joined room {room_name}")

@socketio.on('send_private_message', namespace='/ws/user')
def handle_send_private_message(data):
    """Handle private message sending to specific user"""
    print(f"TEST: send_private_message called with data: {data}")
    target_user_id = data.get('target_user_id')
    message_data = data.get('message_data')
    
    print(f"TEST: target_user_id={target_user_id}, message_data={message_data}")
    
    if target_user_id and message_data:
        # Send message only to the target user's room
        target_room = f'user_{target_user_id}'
        print(f"TEST: Sending message to room: {target_room}")
        
        # CRITICAL FIX: Use broadcast=False to ensure only target room receives message
        emit('private_message', message_data, room=target_room, broadcast=False)
        print(f"TEST: Private message sent to user {target_user_id} in room {target_room}")
        
        # Also send confirmation to sender
        emit('message_sent', {'target_user_id': target_user_id, 'message_data': message_data}, broadcast=False)
    else:
        print(f"TEST: Missing target_user_id or message_data")
        emit('message_error', {'error': 'Missing target_user_id or message_data'}, broadcast=False)

if __name__ == '__main__':
    print("Starting WebSocket room test server...")
    print("Test Instructions:")
    print("1. Connect two clients to /ws/user namespace")
    print("2. Client 1: socket.emit('join_user_room', {user_id: 1})")
    print("3. Client 2: socket.emit('join_user_room', {user_id: 2})")
    print("4. Client 1: socket.emit('send_private_message', {target_user_id: 2, message_data: {text: 'Hello User 2'}})")
    print("5. Only Client 2 should receive the message")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )
