from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from flask import current_app, url_for, request
from models.base import db
from extensions import socketio
from models.user import User
from models.transaction import Transaction
from models.Call import Call  # Import the Call model
from models.message import Message  # Import the Message model
from datetime import datetime
import uuid
import logging
from functools import wraps

# Set up logging
logger = logging.getLogger(__name__)

def socket_auth_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return {'error': 'Authentication required'}, 401
        return f(*args, **kwargs)
    return wrapped

def register_socketio_events():
    """Register all Socket.IO event handlers."""
    
    # Handle connections to /ws/* namespace
    @socketio.on('connect', namespace='/ws')
    def handle_connect_ws():
        try:
            # Get token and user_id from query parameters
            token = request.args.get('token')
            user_id = request.args.get('user_id')
            
            print(f"Connection attempt to /ws namespace with token: {token[:20] if token else None}..., user_id: {user_id}")
            
            # For now, allow connections without tokens for testing
            if user_id:
                join_room(f'user_{user_id}')
                emit('status', {'user_id': user_id, 'status': 'online'}, room=f'user_{user_id}', namespace='/ws')
                print(f"✅ User {user_id} successfully connected to /ws namespace")
                return True
            elif token and user_id:
                # Verify JWT token
                try:
                    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
                    verify_jwt_in_request()
                    token_user_id = get_jwt_identity()
                    
                    if str(token_user_id) == str(user_id):
                        join_room(f'user_{user_id}')
                        emit('status', {'user_id': user_id, 'status': 'online'}, room=f'user_{user_id}', namespace='/ws')
                        print(f"✅ User {user_id} successfully connected to /ws namespace")
                        return True
                    else:
                        print(f"❌ Token user ID {token_user_id} doesn't match requested user ID {user_id}")
                        return False
                        
                except Exception as auth_error:
                    print(f"❌ Token authentication failed: {auth_error}")
                    return False
            else:
                print("❌ Missing user_id in connection request")
                return False
                
        except Exception as e:
            print(f"❌ Error in /ws connect handler: {e}")
            return False
    
    @socketio.on('connect')
    def handle_connect():
        try:
            # Check if user is authenticated via token in connection data
            auth_data = request.args.get('token') if hasattr(request, 'args') else None
            user_id = request.args.get('user_id') if hasattr(request, 'args') else None
            
            if current_user.is_authenticated:
                # Join user room
                join_room(f'user_{current_user.id}')
                emit('status', {'user_id': current_user.id, 'status': 'online'}, room=f'user_{current_user.id}')
                print(f"User {current_user.id} connected to WebSocket (default namespace)")
                return True
            elif auth_data and user_id:
                # Try to authenticate with token
                try:
                    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
                    verify_jwt_in_request()
                    token_user_id = get_jwt_identity()
                    if str(token_user_id) == str(user_id):
                        join_room(f'user_{user_id}')
                        emit('status', {'user_id': user_id, 'status': 'online'}, room=f'user_{user_id}')
                        print(f"User {user_id} connected to WebSocket via token")
                        return True
                except Exception as auth_error:
                    print(f"Token authentication failed: {auth_error}")
            
            print("Unauthenticated WebSocket connection attempt (default namespace)")
            # Allow connection but don't join any rooms
            return True
            
        except Exception as e:
            print(f"Error in connect handler: {e}")
            # Always return True to avoid connection failures during upgrade
            return True

    @socketio.on('disconnect')
    def handle_disconnect():
        try:
            if current_user.is_authenticated:
                leave_room(f'user_{current_user.id}')
                emit('status', {'user_id': current_user.id, 'status': 'offline'}, room=f'user_{current_user.id}')
                print(f"User {current_user.id} disconnected from WebSocket")
            else:
                # Try to get user_id from session or request for anonymous disconnects
                user_id = request.args.get('user_id') if hasattr(request, 'args') else None
                if user_id:
                    leave_room(f'user_{user_id}')
                    print(f"User {user_id} disconnected from WebSocket (anonymous)")
        except Exception as e:
            print(f"Error in disconnect handler: {e}")
            # Don't raise exceptions in disconnect handler

    @socketio.on('join')
    @socket_auth_required
    def on_join(data):
        try:
            room = data.get('room')
            user_id = data.get('user_id')
            
            if not room:
                return {'success': False, 'error': 'Room name is required'}
                
            # Validate that the user is allowed to join this room
            if room.startswith('user_') and user_id:
                room_user_id = room.replace('user_', '')
                if str(user_id) != room_user_id and not current_user.is_authenticated:
                    return {'success': False, 'error': 'Unauthorized'}
            
            join_room(room)
            print(f"User {user_id} joined room: {room}")
            return {'success': True}
            
        except Exception as e:
            print(f"Error in on_join: {str(e)}")
            return {'success': False, 'error': str(e)}

    @socketio.on('leave')
    @socket_auth_required
    def on_leave(data):
        room = data.get('room')
        if room:
            leave_room(room)
            print(f"User {current_user.id} left room: {room}")

@socketio.on('typing')
def handle_typing(data):
    room = data.get('room')
    if room and current_user.is_authenticated:
        emit('user_typing', {
            'user_id': current_user.id,
            'typing': data.get('typing', False)
        }, room=room)

@socketio.on('message')
@socket_auth_required
def handle_message(data):
    """Handle message sending between users"""
    recipient_id = data.get('recipient_id')
    content = data.get('content')
    
    if not recipient_id or not content:
        emit('error', {'message': 'Recipient ID and content are required'}, room=request.sid)
        return
        
    try:
        # Save message to database
        message = Message(
            sender_id=current_user.id,
            receiver_id=recipient_id,
            content=content,
            created_at=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()
        
        # Emit to recipient
        emit('new_message', {
            'id': message.id,
            'sender_id': current_user.id,
            'recipient_id': recipient_id,
            'content': content,
            'timestamp': message.created_at.isoformat(),
            'sender_name': current_user.full_name or current_user.email.split('@')[0],
            'sender_avatar': current_user.photo or url_for('static', filename='img/default-avatar.png')
        }, room=f'user_{recipient_id}')
        
        # Also send back to sender for their own UI update
        emit('new_message', {
            'id': message.id,
            'sender_id': current_user.id,
            'recipient_id': recipient_id,
            'content': content,
            'timestamp': message.created_at.isoformat(),
            'sender_name': current_user.full_name or current_user.email.split('@')[0],
            'sender_avatar': current_user.photo or url_for('static', filename='img/default-avatar.png')
        }, room=f'user_{current_user.id}')
        
    except Exception as e:
        logger.error(f'Error handling message: {str(e)}')
        emit('error', {'message': 'Failed to send message'}, room=request.sid)

@socketio.on('profile_updated')
def handle_profile_updated(data):
    """Handle profile update events"""
    user_id = data.get('user_id')
    if not user_id:
        return
        
    # Forward the event to the specific user's room
    emit('profile_updated', {
        'user_id': user_id,
        'success': data.get('success', True),
        'message': data.get('message', 'Profile updated successfully'),
        'error': data.get('error')
    }, room=f'user_{user_id}')


@socketio.on('initiate_call')
def handle_initiate_call(data):
    """Handle call initiation request"""
    app = current_app._get_current_object()
    
    try:
        if not current_user.is_authenticated:
            emit('call_initiated', {'success': False, 'error': 'Authentication required'}, room=request.sid)
            return
        
        recipient_id = data.get('recipient_id')
        call_type = data.get('type', 'audio')  # audio or video
        
        if not recipient_id:
            emit('call_initiated', {'success': False, 'error': 'Recipient ID is required'}, room=request.sid)
            return
        
        # Immediately acknowledge the call initiation to prevent timeout
        emit('call_initiated', {
            'success': True,
            'message': 'Processing call request...',
            'status': 'processing'
        }, room=request.sid)
        
        # Start a new database session
        with app.app_context():
            recipient = User.query.get(recipient_id)
            if not recipient:
                emit('call_failed', {'error': 'Recipient not found'}, room=request.sid)
                return
            
            # Get call cost (configurable)
            call_cost = 2.5  # ₹2.50 per call
            
            # Check if user has sufficient balance
            if not hasattr(current_user, 'wallet_balance') or current_user.wallet_balance is None:
                current_user.wallet_balance = 0.0
                
            if float(current_user.wallet_balance) < call_cost:
                emit('call_failed', {
                    'error': 'Insufficient balance',
                    'required': call_cost,
                    'current_balance': float(current_user.wallet_balance)
                }, room=request.sid)
                return
    
            # Start a transaction with proper error handling
            try:
                # Get fresh user with row-level lock
                user = User.query.with_for_update().get(current_user.id)
                if not user:
                    raise ValueError('User not found')
                
                # Calculate new balance with proper float handling
                call_cost = round(float(call_cost), 2)
                old_balance = float(user.wallet_balance) if user.wallet_balance is not None else 0.0
                new_balance = round(old_balance - call_cost, 2)
                
                # Generate a unique call ID
                call_id = str(uuid.uuid4())
                
                # Create call record
                call = Call(
                    call_id=call_id,
                    caller_id=current_user.id,
                    callee_id=recipient_id,
                    status='initiated',
                    cost=call_cost
                )
                
                # Create transaction record
                transaction = Transaction(
                    user_id=user.id,
                    amount=-call_cost,  # Negative amount for deduction
                    description=f'Call charge for {call_type} call to {recipient.phone or recipient.email}'
                )
                
                # Add records to session
                db.session.add(call)
                db.session.add(transaction)
                
                # Update user's balance
                user.wallet_balance = new_balance
                db.session.commit()
                
                # Update current_user balance in memory
                current_user.wallet_balance = new_balance
                
                # Log the successful transaction
                logger.info(f'Call charge processed. User: {user.id}, Amount: {call_cost}, New Balance: {new_balance}')
                
                # Notify recipient about the incoming call
                emit('incoming_call', {
                    'caller_id': current_user.id,
                    'caller_name': current_user.full_name or current_user.email.split('@')[0],
                    'call_type': call_type,
                    'call_id': call.call_id,
                    'call_cost': call_cost,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=f'user_{recipient_id}')
                
                # Send success response to caller with phone number
                emit('call_ready', {
                    'success': True,
                    'message': 'Call ready',
                    'call_id': call.call_id,
                    'call_cost': call_cost,
                    'phone_number': recipient.phone,  # Make sure this is the recipient's phone number
                    'new_balance': new_balance,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                db.session.rollback()
                logger.error(f'Error processing call: {str(e)}', exc_info=True)
                emit('call_initiated', {
                    'success': False,
                    'error': f'Failed to initiate call: {str(e)}',
                    'current_balance': float(getattr(current_user, 'wallet_balance', 0.0))
                }, room=request.sid)
    
    except Exception as e:
        logger.error(f'Unexpected error in handle_initiate_call: {str(e)}', exc_info=True)
        emit('call_initiated', {
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }, room=request.sid)
