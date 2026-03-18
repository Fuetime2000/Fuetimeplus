from flask import Blueprint, render_template, request, jsonify, current_app, url_for
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from datetime import datetime

from models.message import Message
from models.user import User
from models.base import db
from extensions import socketio

bp = Blueprint('messages', __name__)

@bp.route('/messages')
@login_required
def messages():
    # Get list of users for the sidebar
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('messages/index.html', users=users)

@bp.route('/messages/<int:recipient_id>')
@login_required
def chat(recipient_id):
    recipient = User.query.get_or_404(recipient_id)
    
    # Mark messages as read
    Message.query.filter_by(
        sender_id=recipient_id,
        receiver_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    # Get message history
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == recipient_id)) |
        ((Message.sender_id == recipient_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()
    
    return render_template('messages/chat.html', 
                         recipient=recipient, 
                         messages=messages)

# Socket events will be registered after app and socketio are fully initialized
# Note: Socket.IO event handlers are now centralized in events.py to avoid conflicts
