"""
This file contains the fixed login endpoint with proper JWT token handling.
Replace the existing login endpoint in api.py with the code from this file.
"""

from datetime import datetime, timedelta
from flask import jsonify, request, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
    verify_jwt_in_request,
    jwt_refresh_token_required
)
from models.user import User
from extensions import db

@api_bp.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
@cross_origin()
def login():
    """
    User login with JWT token generation
    Expected JSON payload:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "device_id": "device_identifier"  # Optional
    }
    """
    # Parse request data
    data = request.get_json(silent=True) or {}
    
    # Log request data for debugging
    current_app.logger.info(f"[LOGIN] Received login request: {data}")
    
    # Validate required fields
    if not data.get('email') or not data.get('password'):
        return jsonify({
            'status': 'error',
            'message': 'Email and password are required'
        }), 400
    
    email = data['email']
    password = data['password']
    
    try:
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        # Check if user exists and password is correct
        if not user or not user.check_password(password):
            current_app.logger.warning(f'Failed login attempt for email: {email}')
            return jsonify({
                'status': 'error',
                'message': 'Invalid email or password'
            }), 401
            
        # Check if account is active
        if not user.active:
            return jsonify({
                'status': 'error',
                'message': 'Account is deactivated. Please contact support.'
            }), 403
            
        # Generate tokens with additional claims
        additional_claims = {
            'user_type': user.user_type,
            'email': user.email,
            'is_verified': user.email_verified,
            'device_id': data.get('device_id')
        }
        
        # Ensure user ID is a string for JWT
        user_id_str = str(user.id) if user.id is not None else None
        if not user_id_str:
            current_app.logger.error('User ID is None during token creation')
            return jsonify({
                'status': 'error',
                'message': 'Failed to create authentication token',
                'code': 'TOKEN_CREATION_ERROR'
            }), 500
        
        # Create tokens with explicit expiration times
        access_token = create_access_token(
            identity=user_id_str,
            additional_claims=additional_claims,
            expires_delta=timedelta(minutes=15)
        )
        
        refresh_token = create_refresh_token(
            identity=user_id_str,
            additional_claims=additional_claims,
            expires_delta=timedelta(days=30)
        )
        
        # Update user's last login and device ID
        user.last_login = datetime.utcnow()
        if 'device_id' in data:
            user.device_id = data['device_id']
        db.session.commit()
        
        # Prepare response
        response = {
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'user_type': user.user_type,
                    'phone': user.phone,
                    'is_verified': user.verified,
                    'email_verified': user.email_verified,
                    'profile_photo': url_for('serve_profile_pic', filename=user.photo, _external=True) 
                                  if hasattr(user, 'photo') and user.photo 
                                  else url_for('static', filename='img/default-avatar.png', _external=True)
                },
                'tokens': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'token_type': 'bearer',
                    'expires_in': 15 * 60,  # 15 minutes in seconds
                    'refresh_expires_in': 30 * 24 * 60 * 60  # 30 days in seconds
                }
            }
        }
        
        current_app.logger.info(f'User {user.id} logged in successfully')
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f'Login error: {str(e)}')
        current_app.logger.error(f'Traceback: {traceback.format_exc()}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during login',
            'error': str(e)
        }), 500
