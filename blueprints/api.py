from datetime import datetime, timedelta, timezone
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, url_for, url_for, send_from_directory, abort, send_file, render_template_string
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import os
from flask_mail import Message as MailMessage
from sqlalchemy import or_, and_, desc, func, delete, update
import hmac
import hashlib
from flask_cors import cross_origin
from extensions import limiter, db, mail
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    jwt_required, 
    get_jwt_identity,
    get_jwt,
    verify_jwt_in_request,
    jwt_required
)

# For refresh token validation
def verify_refresh_token():
    from flask_jwt_extended import verify_jwt_in_request
    return verify_jwt_in_request(refresh=True)

# For backward compatibility
jwt_refresh_token_required = jwt_required(refresh=True)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import timedelta, datetime
import re
import os
import uuid
import json
import math
import time
import base64
from io import BytesIO
from PIL import Image
from functools import wraps
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from sqlalchemy import or_, func, and_
from models.user import User
from models.portfolio import Portfolio, Portfolio as PortfolioModel
from models.contact_request import ContactRequest
from models.review import Review
from models.transaction import Transaction
from models.Call import Call
from models.message import Message
from models.report import Report
from models.saved_user import SavedUser
from models.job_posting import JobPosting
from models.job_request import JobRequest
from extensions import db
from datetime import datetime
from flask import current_app
from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
import traceback
import uuid

# The URL prefix is set in app.py when registering the blueprint
api_bp = Blueprint('api', __name__)
# Explicitly disable CSRF protection for all API endpoints
api_bp.config = {}
api_bp.config['WTF_CSRF_ENABLED'] = False
api_bp.config['WTF_CSRF_CHECK_DEFAULT'] = False

@api_bp.route('/uploads/<path:filename>')
@api_bp.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files from both /api/v1/uploads/ and /static/uploads/"""
    try:
        # Define the base upload directory
        uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        
        # Ensure the uploads directory exists
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Debug information
        current_app.logger.info(f"Looking for file: {filename}")
        current_app.logger.info(f"Application root path: {current_app.root_path}")
        current_app.logger.info(f"Current working directory: {os.getcwd()}")
        current_app.logger.info(f"Uploads directory: {uploads_dir}")
        
        # List files in the uploads directory for debugging
        try:
            files = os.listdir(uploads_dir)
            current_app.logger.info(f"Files in uploads directory: {files}")
            
            # Log if the requested file exists
            file_path = os.path.join(uploads_dir, filename)
            current_app.logger.info(f"Looking for file at: {file_path}")
            current_app.logger.info(f"File exists: {os.path.exists(file_path)}")
            
            # Check if file exists and is accessible
            if os.path.isfile(file_path):
                current_app.logger.info(f"Serving file from: {file_path}")
                return send_from_directory(
                    uploads_dir,
                    filename,
                    as_attachment=False,
                    cache_timeout=31536000  # 1 year cache
                )
            
        except Exception as e:
            current_app.logger.error(f"Error accessing uploads directory: {str(e)}")
            
        # If we get here, file wasn't found
        current_app.logger.error(f"File not found: {filename}")
        current_app.logger.info(f"Current working directory: {os.getcwd()}")
        current_app.logger.info(f"App root path: {current_app.root_path}")
        
        return jsonify({"error": "File not found"}), 404
        
    except Exception as e:
        current_app.logger.error(f"Error in uploaded_file: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# Configure JWT error handlers
@api_bp.errorhandler(422)
def handle_validation_error(err):
    return jsonify({
        'status': 'error',
        'message': 'Validation error',
        'errors': getattr(err, 'data', {}).get('messages', ['Invalid request'])
    }), 422

@api_bp.before_request
def verify_jwt_if_provided():
    # Only verify JWT if Authorization header is present
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        try:
            verify_jwt_in_request(optional=True)
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': 'Invalid or expired token',
                'error': str(e)
            }), 401

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, ""

# Initialize geocoder with timeout and retry settings
geolocator = Nominatim(
    user_agent="fuetime_app",
    timeout=10,  # 10 seconds timeout
    domain="nominatim.openstreetmap.org",
    scheme='https'
)

def clean_location_string(location):
    """Clean and normalize location string for geocoding"""
    if not location or not isinstance(location, str):
        return None
    
    # Basic cleaning
    cleaned = ' '.join(str(location).strip().split())
    
    # Remove any non-printable characters
    cleaned = ''.join(char for char in cleaned if char.isprintable())
    
    # If it's a pincode (6 digits), add India for better results
    if cleaned.isdigit() and len(cleaned) == 6:
        cleaned = f"{cleaned}, India"
    
    return cleaned or None

def get_coordinates(location, max_retries=2):
    """Convert location string to (lat, lng) coordinates with retry logic
    
    Args:
        location: Location string or lat,lng pair
        max_retries: Number of retry attempts
        
    Returns:
        tuple: (latitude, longitude) or None if geocoding fails
    """
    if not location:
        current_app.logger.warning("Empty location provided")
        return None
    
    # Clean the location string
    cleaned_location = clean_location_string(location)
    if not cleaned_location:
        current_app.logger.warning(f"Invalid location after cleaning: {location}")
        return None
    
    current_app.logger.debug(f"Processing location: {cleaned_location}")
    
    # First check if it's already in lat,lng format
    if ',' in cleaned_location:
        try:
            parts = [p.strip() for p in cleaned_location.split(',')]
            if len(parts) == 2:
                lat, lng = map(float, parts)
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    current_app.logger.debug(f"Parsed as coordinates: ({lat}, {lng})")
                    return lat, lng
        except (ValueError, IndexError) as e:
            current_app.logger.debug(f"Not a coordinate, will try geocoding: {e}")
            pass  # Not a valid coordinate, continue with geocoding
    
    # Try geocoding with retries
    for attempt in range(max_retries + 1):
        try:
            current_app.logger.debug(f"Geocoding attempt {attempt + 1} for: {cleaned_location}")
            
            # First try the full location
            location_data = geolocator.geocode(
                cleaned_location,
                exactly_one=True,
                addressdetails=True,
                timeout=10
            )
            
            if location_data:
                coords = (location_data.latitude, location_data.longitude)
                current_app.logger.debug(f"Geocoding successful: {coords}")
                return coords
            
            # If no results, try with a simpler query
            if ' ' in cleaned_location:
                # Try with just the first part of the location (e.g., city name)
                simple_location = cleaned_location.split(',')[0].strip()
                if simple_location and simple_location != cleaned_location:
                    current_app.logger.debug(f"Trying simplified location: {simple_location}")
                    location_data = geolocator.geocode(
                        simple_location,
                        exactly_one=True,
                        timeout=10
                    )
                    if location_data:
                        coords = (location_data.latitude, location_data.longitude)
                        current_app.logger.debug(f"Simplified geocoding successful: {coords}")
                        return coords
            
            current_app.logger.warning(f"No results found for location: {cleaned_location}")
            return None
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            wait_time = 1 * (attempt + 1)  # Exponential backoff
            current_app.logger.warning(
                f"Geocoding attempt {attempt + 1} failed for '{cleaned_location}'. "
                f"Retrying in {wait_time}s. Error: {str(e)}"
            )
            if attempt == max_retries:
                current_app.logger.error(
                    f"Failed to geocode location after {max_retries + 1} attempts: {cleaned_location}"
                )
                return None
            time.sleep(wait_time)
            
        except Exception as e:
            current_app.logger.error(
                f"Unexpected error geocoding '{cleaned_location}': {str(e)}",
                exc_info=True
            )
            return None

def calculate_distance(coord1, coord2):
    """Calculate distance in kilometers between two (lat, lng) coordinates"""
    if not coord1 or not coord2:
        return None
    try:
        return geodesic(coord1, coord2).kilometers
    except Exception as e:
        current_app.logger.error(f"Error calculating distance: {str(e)}")
        return None

def save_base64_image(base64_string, user_id=None):
    """
    Save a base64 encoded image to the server
    
    Args:
        base64_string (str): Base64 encoded image string
        user_id (int, optional): User ID for creating unique filename
        
    Returns:
        str: Relative path to the saved image or None if failed
    """
    try:
        if not base64_string or not isinstance(base64_string, str):
            return None
            
        # Extract the base64 binary data
        if "," in base64_string:
            # Handle data URL format: data:image/png;base64,...
            header, base64_string = base64_string.split(",", 1)
            
        # Decode the base64 string
        image_data = base64.b64decode(base64_string)
        
        # Open the image to validate and process
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary (for PNG with transparency)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        # Generate a unique filename
        filename = f"{uuid.uuid4()}.jpg"
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        
        # Save the image
        image.save(filepath, "JPEG", quality=85)
        
        # Return just the filename - the static URL will be handled by Flask
        return filename
        
    except Exception as e:
        current_app.logger.error(f"Error saving profile image: {str(e)}")
        return None

@api_bp.route('/auth/register', methods=['POST'])
@limiter.limit("10 per minute")  # Slightly higher limit for Flutter app
@cross_origin()
def flutter_register():
    """
    Register a new user from Flutter app with profile image support
    Expected JSON payload:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "full_name": "John Doe",
        "phone": "+1234567890",
        "date_of_birth": "1990-01-01",
        "profession": "Software Developer",
        "experience": "3-5 years",
        "education": "Bachelor's in Computer Science",
        "location": "New York, NY",
        "skills": "Flutter, Python, API Development",
        "payment_type": "hourly",
        "payment_charge": "50.00",
        "profile_image": "base64_encoded_image_string",  # Optional
        "device_id": "device_identifier"  # Optional: For push notifications
    }
    """
    # Debug logging
    current_app.logger.info(f"Flutter registration request headers: {dict(request.headers)}")
    current_app.logger.info(f"Flutter registration content type: {request.content_type}")
    
    try:
        # Parse request data (both JSON and form data)
        if request.content_type and 'application/json' in request.content_type:
            # Handle JSON data
            try:
                data = request.get_json()
                if not data:
                    current_app.logger.error("No JSON data received")
                    return jsonify({
                        'status': 'error',
                        'message': 'No data provided',
                        'code': 'NO_DATA'
                    }), 400
                current_app.logger.info(f"Flutter registration data (JSON): {json.dumps(data, indent=2)}")
            except Exception as e:
                current_app.logger.error(f"Error parsing JSON data: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid JSON data',
                    'code': 'INVALID_JSON'
                }), 400
        else:
            # Handle form data
            data = request.form.to_dict()
            current_app.logger.info(f"Flutter registration data (form): {data}")
            
            # Handle file upload if present
            if 'photo' in request.files and request.files['photo'].filename != '':
                photo = request.files['photo']
                if photo.filename:
                    # Ensure upload folder exists
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    # Save the file and get the path
                    filename = secure_filename(photo.filename)
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    photo.save(filepath)
                    data['profile_image'] = filepath
    except Exception as e:
        current_app.logger.error(f"Error processing request data: {str(e)}")
        current_app.logger.error(traceback.format_exc())  # Log full traceback
        return jsonify({
            'status': 'error',
            'message': 'Error processing request data',
            'code': 'REQUEST_PROCESSING_ERROR',
            'details': str(e)
        }), 400

    # Validate required fields
    required_fields = [
        'email', 'password', 'full_name', 'phone', 
        'date_of_birth', 'work', 'experience',
        'education', 'current_location', 'payment_type'
    ]
    for field in required_fields:
        if field not in data:
            return jsonify({
                'status': 'error',
                'message': f'Missing required field: {field}'
            }), 400
    
    # Validate email format
    if not validate_email(data['email']):
        return jsonify({
            'status': 'error',
            'message': 'Invalid email format'
        }), 400
    
    # Validate password strength
    is_valid, message = validate_password(data['password'])
    if not is_valid:
        return jsonify({
            'status': 'error',
            'message': message
        }), 400
    
    # Check if email or phone already exists with detailed error message
    existing_email = User.query.filter_by(email=data['email']).first()
    existing_phone = User.query.filter_by(phone=data['phone']).first()
    
    if existing_email or existing_phone:
        errors = {}
        if existing_email:
            errors['email'] = 'Email already registered'
        if existing_phone:
            errors['phone'] = 'Phone number already registered'
            
        current_app.logger.warning(f'Registration conflict - Email exists: {bool(existing_email)}, Phone exists: {bool(existing_phone)}')
        return jsonify({
            'status': 'error',
            'message': 'Registration failed',
            'errors': errors
        }), 409
    
    try:
        # Generate username from email if not provided
        username = data.get('username')
        if not username:
            # Use the part before @ in email as username
            username = data['email'].split('@')[0]
            # Remove any non-alphanumeric characters from username
            username = ''.join(c for c in username if c.isalnum() or c in '._-')
            # Ensure username is not empty
            if not username:
                username = f"user_{int(time.time())}"
        
        # Handle profile image if provided
        profile_image_path = None
        if 'profile_image' in data and data['profile_image']:
            profile_image_path = save_base64_image(data['profile_image'], None)
        
        # Prepare user data with proper field mapping
        user_data = {
            'email': data.get('email'),
            'username': username,
            'full_name': data.get('full_name'),
            'phone': data.get('phone'),
            'user_type': 'worker',  # Force all Flutter registrations to be workers
            'work': data.get('work'),  # Map to 'work' field instead of 'profession'
            'experience': data.get('experience'),
            'education': data.get('education'),
            'current_location': data.get('current_location') or data.get('location'),
            'live_location': data.get('live_location'),
            'skills': ', '.join(data.get('skills', [])) if isinstance(data.get('skills'), list) else data.get('skills', ''),
            'payment_type': data.get('payment_type', 'hourly'),
            'payment_charge': float(data.get('payment_charge', 0)) if data.get('payment_charge') else None,
            'photo': profile_image_path,  # This will be just the filename
            'active': True
        }
        
        # Handle date of birth
        if 'date_of_birth' in data and data['date_of_birth']:
            try:
                user_data['date_of_birth'] = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except (ValueError, TypeError) as e:
                current_app.logger.warning(f"Invalid date format for date_of_birth: {data['date_of_birth']}")
                # Set a default date or handle the error as needed
                user_data['date_of_birth'] = None
        
        # Create new user with the prepared data
        user = User(**user_data)
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens with additional claims
        additional_claims = {
            'user_type': user.user_type,
            'email': user.email,
            'is_verified': user.email_verified,
            'device_id': data.get('device_id')
        }
        
        # Create tokens - ensure identity is a string for JWT
        user_id_str = str(user.id) if user.id is not None else None
        if not user_id_str:
            current_app.logger.error('User ID is None during token creation')
            return jsonify({
                'status': 'error',
                'message': 'Failed to create authentication token',
                'code': 'TOKEN_CREATION_ERROR'
            }), 500
            
        current_app.logger.info(f'Creating tokens for user ID: {user_id_str} (type: {type(user_id_str).__name__})')
        
        # Create tokens with string user ID
        access_token = create_access_token(
            identity=user_id_str,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(
            identity=user_id_str,
            additional_claims=additional_claims
        )
        
        # Update user's last login and device ID
        user.last_login = datetime.utcnow()
        if 'device_id' in data:
            user.device_id = data['device_id']
        
        # Create a default portfolio for the user
        portfolio = Portfolio(
            user_id=user.id,
            title=f"{user.full_name}'s Portfolio",
            description=f"Hi, I'm {user.full_name}. Welcome to my portfolio!"
        )
        db.session.add(portfolio)
        db.session.commit()
        
        response = {
            'status': 'success',
            'message': 'User registered successfully via Flutter app',
            'data': {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'user_type': user.user_type,
                    'phone': user.phone,
                    'is_verified': user.verified,
                    'email_verified': user.email_verified,
                    'profile_photo': url_for('serve_profile_pic', filename=user.photo, _external=True) if hasattr(user, 'photo') and user.photo else url_for('static', filename='img/default-avatar.png', _external=True)
                },
                'tokens': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'token_type': 'bearer',
                    'expires_in': 3153600000  # 100 years in seconds
                }
            }
        }
        
        # Add CORS headers for Flutter app
        response = jsonify(response)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response, 201
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_trace = traceback.format_exc()
        current_app.logger.error(f'Registration error: {str(e)}\n{error_trace}')
        
        # Create a more user-friendly error message
        error_message = 'An error occurred during registration. Please try again.'
        error_details = str(e)
        
        # Handle common database errors
        error_code = 'REGISTRATION_ERROR'
        if 'UNIQUE constraint failed' in error_details or 'duplicate key' in error_details.lower():
            if 'email' in error_details.lower():
                error_message = 'This email is already registered.'
                error_code = 'EMAIL_EXISTS'
            elif 'phone' in error_details.lower():
                error_message = 'This phone number is already registered.'
                error_code = 'PHONE_EXISTS'
        
        # Create error response with CORS headers
        error_response = jsonify({
            'status': 'error',
            'message': error_message,
            'code': error_code,
            'error': error_details if current_app.debug else None
        })
        
        # Add CORS headers
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        error_response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        error_response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        
        return error_response, 500

@api_bp.route('/auth/refresh', methods=['POST'])
@cross_origin()
def refresh():
    """
    Refresh access token using refresh token
    Expected JSON payload:
    {
        "refresh_token": "refresh_token_here"
    }
    Or refresh token in Authorization header as: Bearer <refresh_token>
    """
    try:
        # Try to get refresh token from request body first
        data = request.get_json()
        refresh_token = data.get('refresh_token') if data else None
        
        if refresh_token:
            # Manually verify the refresh token from body
            try:
                from flask_jwt_extended import decode_token
                decoded = decode_token(refresh_token)
                
                # Check if it's a refresh token
                if decoded.get('type') != 'refresh':
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid token type. Expected refresh token.'
                    }), 401
                
                user_id = decoded.get('sub')
            except Exception as token_error:
                current_app.logger.error(f'Invalid refresh token: {str(token_error)}')
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid or expired refresh token',
                    'error': str(token_error)
                }), 401
        else:
            # Fall back to header/cookie method
            verify_refresh_token()
            user_id = get_jwt_identity()
        
        # Get the user from database
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
            
        # Create new access token
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'user_type': user.user_type,
                'email': user.email,
                'is_verified': user.email_verified,
                'device_id': user.device_id
            }
        )
        
        return jsonify({
            'status': 'success',
            'access_token': access_token,
            'token_type': 'bearer',
            'expires_in': 3153600000  # 100 years in seconds
        })
        
    except Exception as e:
        current_app.logger.error(f'Token refresh error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to refresh token',
            'error': str(e)
        }), 401


@api_bp.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limiting
@cross_origin()
def login():
    """
    User login
    Expected JSON payload:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "device_id": "device_identifier"  # Optional: For push notifications
    }
    """
    # Debug logging
    current_app.logger.info(f"[LOGIN] Incoming request headers: {dict(request.headers)}")
    current_app.logger.info(f"[LOGIN] Request content type: {request.content_type}")
    
    # Get request data based on content type
    if 'application/json' in request.content_type:
        try:
            # Try to parse JSON data
            data = request.get_json(force=True, silent=True)
            if data is None:
                # If get_json returns None, try to parse manually
                raw_data = request.get_data(as_text=True)
                if raw_data:
                    data = json.loads(raw_data)
            current_app.logger.info(f"[LOGIN] Received JSON data: {data}")
        except Exception as e:
            current_app.logger.error(f"[LOGIN] Error parsing JSON data: {str(e)}")
            data = {}
    else:
        data = request.form.to_dict()
        current_app.logger.info(f"[LOGIN] Received form data: {data}")
    
    # Log raw request data
    try:
        raw_data = request.get_data(as_text=True)
        current_app.logger.info(f"[LOGIN] Raw request data: {raw_data}")
    except Exception as e:
        current_app.logger.error(f"[LOGIN] Error reading raw request data: {str(e)}")
    
    # If no data was found, try to parse it manually
    if not data and request.method == 'POST':
        try:
            data = json.loads(request.get_data(as_text=True))
            current_app.logger.info(f"[LOGIN] Manually parsed JSON data: {data}")
        except Exception as e:
            current_app.logger.error(f"[LOGIN] Error parsing request data: {str(e)}")
            data = {}
    
    current_app.logger.info(f"[LOGIN] Final data being processed: {data}")
    
    # Validate required fields
    if not data or 'email' not in data or 'password' not in data:
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
        
        # Create tokens - ensure identity is a string for JWT
        user_id_str = str(user.id) if user.id is not None else None
        if not user_id_str:
            current_app.logger.error('User ID is None during token creation')
            return jsonify({
                'status': 'error',
                'message': 'Failed to create authentication token',
                'code': 'TOKEN_CREATION_ERROR'
            }), 500
            
        current_app.logger.info(f'Creating tokens for user ID: {user_id_str} (type: {type(user_id_str).__name__})')
        
        # Create tokens with string user ID
        access_token = create_access_token(
            identity=user_id_str,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(
            identity=user_id_str,
            additional_claims=additional_claims
        )
        
        # Update user's last login and device ID
        user.last_login = datetime.utcnow()
        if 'device_id' in data:
            user.device_id = data['device_id']
        db.session.commit()
        
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
                    'profile_photo': url_for('serve_profile_pic', filename=user.photo, _external=True) if hasattr(user, 'photo') and user.photo else url_for('static', filename='img/default-avatar.png', _external=True)
                },
                'tokens': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'token_type': 'bearer',
                    'expires_in': 3153600000  # 100 years in seconds
                }
            }
        }
        
        current_app.logger.info(f'User {user.id} logged in successfully')
        return jsonify(response)
        
    except Exception as e:
        import traceback
        current_app.logger.error(f'Login error: {str(e)}')
        current_app.logger.error(f'Traceback: {traceback.format_exc()}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during login',
            'error': str(e),
            'debug': current_app.debug  # Only include in development
        }), 500

@api_bp.route('/api/calculate-distance', methods=['GET', 'POST'])
@jwt_required(optional=True)  # Make JWT optional for flexibility
@cross_origin()  # Enable CORS for Flutter
@limiter.limit("100 per day")  # Add rate limiting
def calculate_distance_endpoint():
    """
    Calculate distance between two locations
    
    Supports both GET and POST methods for better compatibility
    
    GET Parameters / POST JSON:
    - from: Location string (e.g., 'New York, NY') or lat,lng (e.g., '40.7128,-74.0060')
    - to: Location string or lat,lng of destination
    - unit: Optional, 'km' or 'mi' (default: 'km')
    - format: Optional, 'full' (default) or 'simple' (just returns the distance)
    
    Returns:
    {
        'success': bool,
        'distance': float,  # distance in requested unit
        'distance_km': float,  # always in kilometers
        'distance_mi': float,  # always in miles
        'distance_display': str,  # formatted string (e.g., '1.2 km away')
        'from': {
            'address': str,
            'coordinates': [lat, lng]
        },
        'to': {
            'address': str,
            'coordinates': [lat, lng]
        },
        'unit': str  # the unit used in response
    }
    """
    # Get parameters from either GET or POST
    if request.method == 'POST':
        data = request.get_json() or {}
        from_location = data.get('from')
        to_location = data.get('to')
        unit = data.get('unit', 'km').lower()
        response_format = data.get('format', 'full')
    else:  # GET
        from_location = request.args.get('from')
        to_location = request.args.get('to')
        unit = request.args.get('unit', 'km').lower()
        response_format = request.args.get('format', 'full')
    
    # Validate unit
    if unit not in ('km', 'mi'):
        unit = 'km'
    
    current_app.logger.info(f"Distance calculation request - from: '{from_location}', to: '{to_location}'")
    
    # Validate required parameters
    if not from_location or not to_location:
        error_msg = f"Missing required parameters. from: '{from_location}', to: '{to_location}'"
        current_app.logger.warning(error_msg)
        return jsonify({
            'success': False,
            'error': 'Both from and to locations are required',
            'details': error_msg
        }), 400
    
    try:
        # Get coordinates for both locations
        current_app.logger.info("Getting coordinates for locations...")
        
        def get_location_info(location):
            """Helper to get both coordinates and address for a location"""
            coords = get_coordinates(location)
            if not coords:
                return None, None, f"Could not determine coordinates for: '{location}'"
                
            # Try to get address if it's coordinates
            address = location
            if isinstance(location, str) and ',' in location and all(x.strip().replace('.', '').replace('-', '').isdigit() for x in location.split(',')):
                try:
                    geo = geolocator.reverse(f"{coords[0]}, {coords[1]}", exactly_one=True)
                    if geo:
                        address = geo.address
                except Exception as e:
                    current_app.logger.warning(f"Could not reverse geocode {coords}: {str(e)}")
            
            return coords, address, None
        
        # Get coordinates and addresses
        from_coords, from_address, from_error = get_location_info(from_location)
        to_coords, to_address, to_error = get_location_info(to_location)
        
        # Check for errors
        errors = []
        if from_error:
            errors.append(from_error)
        if to_error:
            errors.append(to_error)
            
        if errors:
            return jsonify({
                'success': False,
                'error': 'Location resolution failed',
                'details': '; '.join(errors),
                'from_location': from_location,
                'to_location': to_location
            }), 400
        
        # Calculate distance in kilometers
        distance_km = calculate_distance(from_coords, to_coords)
        distance_mi = distance_km * 0.621371  # Convert to miles
        
        # Format distance display
        if unit == 'mi':
            distance_value = distance_mi
            if distance_mi < 0.1:  # Less than 0.1 miles (~160m)
                distance_ft = int(distance_mi * 5280)  # Convert to feet
                distance_display = f"{distance_ft} feet away"
            elif distance_mi < 1:  # Less than 1 mile
                distance_display = f"{distance_mi:.1f} miles away"
            else:  # 1 mile or more
                distance_display = f"{distance_mi:.1f} miles away"
        else:  # Default to kilometers
            distance_value = distance_km
            if distance_km < 0.1:  # Less than 100m
                distance_m = int(distance_km * 1000)
                distance_display = f"{distance_m}m away"
            elif distance_km < 1:  # Less than 1km
                distance_display = f"{distance_km:.1f}km away"
            else:  # 1km or more
                distance_display = f"{distance_km:.1f}km away"
        
        # Prepare response
        response = {
            'success': True,
            'distance': distance_value,
            'distance_km': distance_km,
            'distance_mi': distance_mi,
            'distance_display': distance_display,
            'unit': unit,
            'from': {
                'address': from_address,
                'coordinates': from_coords
            },
            'to': {
                'address': to_address,
                'coordinates': to_coords
            }
        }
        
        # Return simplified response if requested
        if response_format == 'simple':
            return jsonify({
                'success': True,
        
            'details': str(ve)
        }), 400
    except Exception as e:
        error_msg = f"Error calculating distance: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to calculate distance',
            'details': str(e)
        }), 500

def handle_profile_photo_upload():
    """
    Helper function to handle profile photo upload
    Supports multiple field names: 'photo', 'profile_image', and 'file'
    Handles 'subject' field if present in various formats
    """
    try:
        current_app.logger.info("\n" + "="*80)
        current_app.logger.info("=== START PROFILE PHOTO UPLOAD PROCESSING ===")
        
        # Log all request details
        current_app.logger.info(f"Request Method: {request.method}")
        current_app.logger.info(f"Request URL: {request.url}")
        current_app.logger.info(f"Content Type: {request.content_type}")
        current_app.logger.info(f"Content Length: {request.content_length} bytes")
        
        # Log all headers
        current_app.logger.info("\n=== REQUEST HEADERS ===")
        for header, value in request.headers.items():
            current_app.logger.info(f"{header}: {value}")
        
        # Log URL parameters
        current_app.logger.info("\n=== URL PARAMETERS ===")
        for arg, value in request.args.items():
            current_app.logger.info(f"{arg}: {value} (type: {type(value).__name__})")
        
        # Log form data
        current_app.logger.info("\n=== FORM DATA ===")
        for key, value in request.form.items():
            current_app.logger.info(f"{key}: {value} (type: {type(value).__name__})")
        
        # Log files
        current_app.logger.info("\n=== FILES ===")
        for field_name, file in request.files.items():
            current_app.logger.info(f"File Field: {field_name}")
            current_app.logger.info(f"  Filename: {file.filename}")
            current_app.logger.info(f"  Content Type: {file.content_type}")
            current_app.logger.info(f"  Content Length: {file.content_length} bytes")
            
            # Log first 100 bytes of file
            try:
                file.seek(0)
                file_header = file.read(100)
                current_app.logger.info(f"  File header (first 100 bytes): {file_header}")
                file.seek(0)  # Reset file pointer
            except Exception as e:
                current_app.logger.error(f"  Error reading file header: {e}")
        
        # Handle subject field if present (some clients send this in different ways)
        subject = None
        
        # Check for subject in headers first (common in mobile apps)
        if 'Subject' in request.headers:
            subject = request.headers.get('Subject')
            current_app.logger.info(f"\n[1/4] Got subject from headers: {repr(subject)} (type: {type(subject).__name__})")
        # 1. Try to get subject from URL parameters
        elif 'subject' in request.args:
            subject = request.args.get('subject')
            current_app.logger.info(f"\n[2/4] Got subject from URL parameters: {repr(subject)} (type: {type(subject).__name__})")
        # 2. Then try to get from form data
        elif 'subject' in request.form:
            subject = request.form['subject']
            current_app.logger.info(f"\n[3/4] Got subject from form data: {repr(subject)} (type: {type(subject).__name__})")
        # 3. Then try to get from JSON data if present in form
        elif 'data' in request.form:
            try:
                data = json.loads(request.form['data'])
                subject = data.get('subject')
                if subject is not None:
                    current_app.logger.info(f"\n[4/4] Got subject from JSON data: {repr(subject)} (type: {type(subject).__name__})")
            except (json.JSONDecodeError, AttributeError) as e:
                current_app.logger.warning(f"Failed to parse JSON data: {e}")
        
        # Process the subject if found
        if subject is not None:
            current_app.logger.info(f"\n=== PROCESSING SUBJECT ===")
            current_app.logger.info(f"Raw subject: {repr(subject)} (type: {type(subject).__name__})")
            
            # Ensure subject is a string if it exists
            if not isinstance(subject, str):
                try:
                    subject = str(subject)
                    current_app.logger.info(f"Converted subject to string: {repr(subject)}")
                except Exception as e:
                    current_app.logger.error(f"Failed to convert subject to string: {e}")
                    subject = "profile_photo_upload"
                    current_app.logger.info(f"Using default subject: {subject}")
        else:
            current_app.logger.info("\nNo subject found in request headers, URL params, form data, or JSON - this is normal for profile uploads")
            subject = "profile_photo_upload"
            
        current_app.logger.info(f"\n=== FINAL SUBJECT ===")
        current_app.logger.info(f"Subject being used: {repr(subject)} (type: {type(subject).__name__})")
        
        # Log file validation
        if not request.files:
            current_app.logger.error("\n!!! NO FILES FOUND IN REQUEST !!!")
        else:
            current_app.logger.info("\n=== FILE VALIDATION ===")
            for field_name, file in request.files.items():
                current_app.logger.info(f"Validating file in field: {field_name}")
                if not file.filename:
                    current_app.logger.error(f"  - No filename provided in field: {field_name}")
                
                # More flexible content type validation
                is_valid_content_type = (
                    file.content_type and (
                        file.content_type.startswith('image/') or
                        file.content_type == 'application/octet-stream'
                    )
                )
                if not is_valid_content_type:
                    current_app.logger.warning(f"  - Invalid content type: {file.content_type} in field: {field_name}")
                
                # Check file size by reading the file stream instead of relying on content_length
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size <= 0:
                    current_app.logger.error(f"  - Empty file in field: {field_name} (size: {file_size} bytes)")
                else:
                    current_app.logger.info(f"  - File size: {file_size} bytes in field: {field_name}")
        
        current_app.logger.info("\n=== END PROFILE PHOTO UPLOAD PROCESSING ===\n")
        
        # Check if we have any files to process
        if not request.files:
            raise ValueError("No files were uploaded")
            
        # Find the first valid file field
        file_field = None
        file_fields_to_try = ['photo', 'profile_image', 'file']
        for field in file_fields_to_try:
            if field in request.files:
                file_field = field
                break
                
        if not file_field:
            raise ValueError("No valid file field found. Expected one of: " + ", ".join(file_fields_to_try))
            
        file = request.files[file_field]
        if not file or not file.filename:
            raise ValueError("No file selected or file has no name")
            
        # Rest of your file processing logic here...
        
        # Check for file in different possible field names (in order of priority)
        file_field = None
        file_fields_to_try = ['photo', 'profile_image', 'file']
        
        for field in file_fields_to_try:
            if field in request.files:
                file_field = field
                break
        
        if not file_field:
            current_app.logger.error("No valid file field found in request.files")
            return {
                'status': 'error',
                'message': 'No file provided. Please include a file with the field name: ' + ', '.join(file_fields_to_try),
                'code': 400
            }
            
        photo = request.files[file_field]
        current_app.logger.info(f"Processing file: {photo.filename} from field: {file_field}")
        
        # Check if the post request has the file part
        if not photo or photo.filename == '':
            current_app.logger.error("No file selected or empty file")
            return {
                'status': 'error',
                'message': 'No file selected',
                'code': 400
            }
            
        # Validate file size by reading the stream
        photo.seek(0, 2)  # Seek to end
        file_size = photo.tell()
        photo.seek(0)  # Reset to beginning
        
        if file_size <= 0:
            current_app.logger.error(f"Empty file detected: {file_size} bytes")
            return {
                'status': 'error',
                'message': 'Empty file uploaded',
                'code': 400
            }
            
        current_app.logger.info(f"File size validated: {file_size} bytes")
            
        if photo:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            # Validate file type by checking file signature (magic bytes)
            photo.seek(0)
            file_header = photo.read(10)
            photo.seek(0)  # Reset to beginning
            
            # Check for common image file signatures
            is_valid_image = (
                file_header.startswith(b'\x89PNG') or  # PNG
                file_header.startswith(b'\xff\xd8\xff') or  # JPEG
                file_header.startswith(b'GIF87a') or  # GIF87a
                file_header.startswith(b'GIF89a') or  # GIF89a
                file_header.startswith(b'RIFF') and b'WEBP' in file_header  # WebP
            )
            
            if not is_valid_image:
                current_app.logger.error(f"Invalid image file signature: {file_header}")
                return {
                    'status': 'error',
                    'message': 'Invalid image file. Please upload a valid PNG, JPEG, GIF, or WebP image.',
                    'code': 400
                }
            
            # Generate unique filename
            filename = secure_filename(photo.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            # Determine extension from file signature if not present or incorrect
            if not ext or ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
                if file_header.startswith(b'\x89PNG'):
                    ext = 'png'
                elif file_header.startswith(b'\xff\xd8\xff'):
                    ext = 'jpg'
                elif file_header.startswith(b'GIF'):
                    ext = 'gif'
                elif b'WEBP' in file_header:
                    ext = 'webp'
                else:
                    ext = 'jpg'  # Default fallback
                    
            current_app.logger.info(f"Using file extension: {ext}")
                
            new_filename = f"{uuid.uuid4()}.{ext}"
            
            # Ensure upload directory exists
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pics')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            photo_path = os.path.join(upload_dir, new_filename)
            photo.save(photo_path)
            
            # Remove old photo if exists
            old_photo_path = None
            if user.photo:
                # Handle both full paths and filenames
                old_photo_name = os.path.basename(user.photo)
                old_photo_path = os.path.join(upload_dir, old_photo_name)
                
                # Also check in the root uploads directory for backward compatibility
                if not os.path.exists(old_photo_path):
                    old_photo_path = os.path.join(current_app.root_path, 'static', 'uploads', old_photo_name)
                
                if os.path.exists(old_photo_path):
                    try:
                        os.remove(old_photo_path)
                    except Exception as e:
                        current_app.logger.error(f"Error removing old photo: {str(e)}")
            
            # Update user's photo - store just the filename, not the full path
            user.photo = new_filename
            db.session.commit()
            
            # Generate URL using the serve_profile_pic route
            photo_url = url_for('serve_profile_pic', filename=new_filename, _external=True)
            
            # Log the generated URL for debugging
            current_app.logger.info(f"Generated photo URL: {photo_url}")
            
            return {
                'status': 'success',
                'message': 'Profile photo updated successfully',
                'photo_url': photo_url,
                'code': 200
            }
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading profile photo: {str(e)}")
        return {
            'status': 'error',
            'message': 'Failed to upload profile photo',
            'error': str(e),
            'code': 500
        }

@api_bp.route('/profile/photo', methods=['POST'])
@jwt_required()
def upload_profile_photo():
    """
    Upload or update user's profile photo
    """
    result = handle_profile_photo_upload()
    return jsonify({k: v for k, v in result.items() if k != 'code'}), result.get('code', 500)

@api_bp.route('/account/profile-image', methods=['POST'])
@jwt_required()
def upload_profile_image():
    """
    Upload or update user's profile image (v1 API endpoint)
    This is an alias for /profile/photo to maintain backward compatibility
    
    Expects a multipart/form-data request with an image file in one of these fields:
    - photo
    - profile_image
    - file
    
    Handles the 'subject' field that might be sent in various formats:
    - URL parameter: ?subject=value
    - Form field: subject=value
    - Nested in JSON: data={"subject":"value"}
    
    Returns:
        JSON response with status, message, and photo_url on success
    """
    try:
        # Log detailed request information
        current_app.logger.info("\n" + "="*50)
        current_app.logger.info("===== New Profile Image Upload Request =====")
        current_app.logger.info(f"Request method: {request.method}")
        current_app.logger.info(f"Endpoint: {request.path}")
        
        # Call the helper function to handle the upload
        result = handle_profile_photo_upload()
        
        # Log the result before returning
        current_app.logger.info(f"Upload result: {result}")
        
        # Return the response with the appropriate status code
        response_data = {k: v for k, v in result.items() if k != 'code'}
        return jsonify(response_data), result.get('code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error in upload_profile_image: {str(e)}")
        
        # Log request details for debugging
        try:
            raw_data = request.get_data(as_text=True)
            current_app.logger.info(f"Raw request data (first 1000 chars): {raw_data[:1000] if raw_data else 'No data'}")
        except Exception as debug_e:
            current_app.logger.warning(f"Could not read raw request data: {str(debug_e)}")
            
        # Log each file's details
        for key, file in request.files.items():
            current_app.logger.info(f"File '{key}': {file.filename}, {file.content_type}, {file.content_length} bytes")
            
        # Log each form field
        for key, value in request.form.items():
            current_app.logger.info(f"Form field '{key}': {value}")
            
        # Check content type
        if not request.content_type or 'multipart/form-data' not in request.content_type:
            error_msg = f"Invalid content type: {request.content_type}. Expected multipart/form-data"
            current_app.logger.error(error_msg)
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 415  # Unsupported Media Type
            
        # Check if request has files data
        if not request.files:
            error_msg = "No files found in the request"
            current_app.logger.error(error_msg)
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 400
        
        # Handle the image upload
        result = handle_profile_photo_upload()
        
        # Log the result before returning
        current_app.logger.info(f"Profile image upload result: {result}")
        current_app.logger.info("===== End of Profile Image Upload Request =====")
        
        return jsonify({k: v for k, v in result.items() if k != 'code'}), result.get('code', 500)
        
    except Exception as e:
        current_app.logger.error(f"Error in upload_profile_image: {str(e)}", exc_info=True)
        current_app.logger.error(f"Request data: {request.get_data()}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while processing your request',
            'error': str(e)
        }), 500

def get_portfolio_response(portfolio):
    """Helper function to format portfolio response"""
    if not portfolio:
        return None
        
    return {
        'id': portfolio.id,
        'user_id': portfolio.user_id,
        'bio': portfolio.bio,
        'skills': portfolio.skills.split(',') if portfolio.skills else [],
        'experience': portfolio.experience,
        'education': portfolio.education,
        'certifications': portfolio.certifications,
        'languages': portfolio.languages.split(',') if portfolio.languages else [],
        'hourly_rate': float(portfolio.hourly_rate) if portfolio.hourly_rate else None,
        'portfolio_url': portfolio.portfolio_url,
        'created_at': portfolio.created_at.isoformat() if portfolio.created_at else None,
        'updated_at': portfolio.updated_at.isoformat() if portfolio.updated_at else None
    }

# Wallet API Endpoints
@api_bp.route('/wallet', methods=['GET'])
@jwt_required()
def get_wallet():
    """
    Get user's wallet balance and recent transactions
    Query Parameters:
    - limit: Number of transactions to return (default: 10, max: 50)
    - offset: Number of transactions to skip (for pagination, default: 0)
    """
    try:
        # Get JWT identity
        try:
            user_id = get_jwt_identity()
            if not user_id:
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401
        except Exception as e:
            current_app.logger.error(f'JWT validation error: {str(e)}')
            return jsonify({
                'status': 'error',
                'message': 'Invalid or expired token',
                'code': 'INVALID_TOKEN'
            }), 401

        # Get and validate query parameters
        try:
            limit = min(int(request.args.get('limit', 10)), 50)
            offset = max(int(request.args.get('offset', 0)), 0)
        except (TypeError, ValueError) as e:
            return jsonify({
                'status': 'error',
                'message': 'Invalid limit or offset parameter',
                'code': 'INVALID_PARAMETER'
            }), 400
        
        # Verify user exists and get wallet balance
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    'status': 'error',
                    'message': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 404
            
            # Get recent transactions
            transactions = Transaction.query.filter_by(
                user_id=user_id
            ).order_by(
                Transaction.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            # Format transactions
            transactions_data = [{
                'id': str(txn.id) if txn.id else None,
                'amount': float(txn.amount) if txn.amount is not None else 0.0,
                'description': str(txn.description) if txn.description else '',
                'status': str(txn.status) if txn.status else 'completed',
                'reference_id': str(txn.reference_id) if txn.reference_id else None,
                'created_at': txn.created_at.isoformat() if txn.created_at else None,
                'updated_at': txn.updated_at.isoformat() if txn.updated_at else None
            } for txn in transactions]
            
            return jsonify({
                'status': 'success',
                'data': {
                    'balance': float(user.wallet_balance) if user.wallet_balance is not None else 0.0,
                    'currency': 'INR',
                    'transactions': transactions_data,
                    'pagination': {
                        'limit': limit,
                        'offset': offset,
                        'total': Transaction.query.filter_by(user_id=user_id).count()
                    }
                }
            })
            
        except Exception as e:
            current_app.logger.error(f'Database error in get_wallet: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': 'Database error occurred',
                'code': 'DATABASE_ERROR'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f'Unexpected error in get_wallet: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_SERVER_ERROR'
        }), 500

@api_bp.route('/wallet/verify-payment', methods=['POST'])
@jwt_required()
def verify_wallet_payment():
    """
    Verify a wallet payment and update the wallet balance
    Expected JSON payload:
    {
        "razorpay_payment_id": "pay_XXXXXXXXXXXXXX",
        "razorpay_order_id": "order_XXXXXXXXXXXXXX",
        "razorpay_signature": "XXXXXXXXXXXXXX",
        "amount": 100.00,
        "currency": "INR"
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            current_app.logger.error('No data provided in request')
            return jsonify({
                'status': 'error',
                'message': 'No data provided',
                'code': 'MISSING_DATA'
            }), 400
            
        current_app.logger.info(f'Received payment verification request data: {data}')
            
        # Get required fields
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        amount = data.get('amount')
        currency = data.get('currency', 'INR')
        
        # Log the received values for debugging
        current_app.logger.info(f'Extracted values - Payment ID: {razorpay_payment_id}, Order ID: {razorpay_order_id}, ' 
                              f'Signature: {razorpay_signature}, Amount: {amount}, Currency: {currency}')
        
        # Validate required fields with detailed error messages
        missing_fields = []
        if not razorpay_payment_id:
            missing_fields.append('razorpay_payment_id')
        if not razorpay_order_id:
            missing_fields.append('razorpay_order_id')
        if not razorpay_signature:
            missing_fields.append('razorpay_signature')
        if amount is None:
            missing_fields.append('amount')
            
        if missing_fields:
            error_msg = f'Missing required fields: {", ".join(missing_fields)}'
            current_app.logger.error(error_msg)
            return jsonify({
                'status': 'error',
                'message': error_msg,
                'code': 'MISSING_REQUIRED_FIELDS',
                'missing_fields': missing_fields
            }), 400
            
        # Get Razorpay configuration
        razorpay_key_id = current_app.config.get('RAZORPAY_KEY_ID')
        razorpay_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
        
        # Log configuration status for debugging
        current_app.logger.info(f'Razorpay Config - Key ID: {razorpay_key_id[:8]}...' if razorpay_key_id else 'Key ID: Not Set')
        current_app.logger.info('Razorpay Secret: ' + ('Set' if razorpay_secret else 'Not Set'))
        
        if not all([razorpay_key_id, razorpay_secret]):
            current_app.logger.error('Razorpay configuration incomplete')
            missing = []
            if not razorpay_key_id:
                missing.append('RAZORPAY_KEY_ID')
            if not razorpay_secret:
                missing.append('RAZORPAY_KEY_SECRET')
                
            return jsonify({
                'status': 'error',
                'message': 'Payment verification service not available',
                'code': 'SERVICE_UNAVAILABLE',
                'missing_config': missing,
                'hint': 'Please ensure both RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are set in your environment variables'
            }), 503
            
        # Verify the payment signature
        try:
            current_app.logger.info(f'Verifying payment: Order={razorpay_order_id}, Payment={razorpay_payment_id}')
            
            # Create the expected signature
            payload = f"{razorpay_order_id}|{razorpay_payment_id}"
            current_app.logger.debug(f'Signature payload: {payload}')
            
            try:
                generated_signature = hmac.new(
                    razorpay_secret.encode('utf-8'),
                    payload.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                current_app.logger.debug(f'Generated signature: {generated_signature[:8]}...')
                current_app.logger.debug(f'Received signature: {razorpay_signature[:8]}...')
            except Exception as e:
                current_app.logger.error(f'Error generating signature: {str(e)}')
                raise

            # Verify the signature
            if not hmac.compare_digest(generated_signature, razorpay_signature):
                current_app.logger.warning('Signature verification failed')
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid payment signature',
                    'code': 'INVALID_SIGNATURE',
                    'hint': 'The payment signature could not be verified. Please ensure the payment details are correct.'
                }), 400
                
        except Exception as e:
            current_app.logger.error(f'Error verifying payment signature: {str(e)}')
            return jsonify({
                'status': 'error',
                'message': 'Error verifying payment',
                'code': 'VERIFICATION_ERROR'
            }), 500
            
        # Start database transaction
        db_session = db.session
        db_session.begin_nested()
        
        try:
            # Get user with row-level lock to prevent race conditions
            user = User.query.with_for_update().get(user_id)
            if not user:
                return jsonify({
                    'status': 'error',
                    'message': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 404
                
            # Get current balance
            old_balance = float(user.wallet_balance) if user.wallet_balance is not None else 0.0
        
            # Get processing fee from request or calculate it
            PROCESSING_FEE = 1.00  # Rs. 1 processing fee
            amount_after_fee = max(0, amount - PROCESSING_FEE)
        
            # Calculate new balance (add amount after fee)
            new_balance = round(old_balance + amount_after_fee, 2)

            # Update user's balance
            user.wallet_balance = new_balance
            
            # Create transaction record
            transaction = Transaction(
                user_id=user.id,
                amount=amount_after_fee,  # Store the amount after fee
                description=f'Wallet top-up via Razorpay (Rs. {amount} - Rs. {PROCESSING_FEE} fee)',
                status='completed',
                reference_id=razorpay_payment_id,
                metadata={
                    'payment_gateway': 'razorpay',
                    'order_id': razorpay_order_id,
                    'currency': currency,
                    'original_amount': amount,
                    'processing_fee': PROCESSING_FEE,
                    'amount_after_fee': amount_after_fee,
                    'verified_at': datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Add transaction to session
            db_session.add(transaction)
            db_session.add(user)
            
            # Commit the transaction
            db_session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'payment_id': razorpay_payment_id,
                    'order_id': razorpay_order_id,
                    'amount': amount_after_fee,
                'processing_fee': PROCESSING_FEE,
                'original_amount': amount,
                    'currency': currency,
                    'wallet_balance': new_balance,
                    'transaction_id': transaction.id,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }), 200
            
        except Exception as e:
            db_session.rollback()
            current_app.logger.error(f'Error processing wallet top-up: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': 'Failed to process wallet top-up',
                'code': 'PROCESSING_ERROR'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f'Error in verify_wallet_payment: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_SERVER_ERROR'
        }), 500


@api_bp.route('/wallet/add', methods=['POST'])
@jwt_required()
def add_to_wallet():
    """
    Add money to wallet
    Expected JSON payload:
    {
        "amount": 100.00,
        "description": "Wallet top-up"
    }
    """
    db_session = db.session
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
            
        amount = data.get('amount')
        description = data.get('description', 'Wallet top-up')
        
        # Validate amount
        try:
            amount = float(amount)
            
            # Enforce minimum top-up amount of Rs. 1
            MIN_TOPUP_AMOUNT = 1.00
            
            if amount < MIN_TOPUP_AMOUNT:
                raise ValueError(f'Minimum top-up amount is Rs. {MIN_TOPUP_AMOUNT:.2f}')
            
            # No processing fee applied
            original_amount = amount
            current_app.logger.info(f'Adding amount to wallet: Rs. {amount:.2f} (no processing fee)')
        except (TypeError, ValueError) as e:
            return jsonify({
                'status': 'error',
                'message': 'Invalid amount provided'
            }), 400
        
        # Start a new transaction
        db_session.begin_nested()
        
        try:
            # Get user with row-level lock to prevent race conditions
            user = User.query.with_for_update().get(user_id)
            if not user:
                raise ValueError('User not found')
                
            # Get current balance
            old_balance = float(user.wallet_balance) if user.wallet_balance is not None else 0.0
            
            # Calculate new balance with proper float handling
            amount = round(amount, 2)  # amount is already a float after processing
            new_balance = round(old_balance + amount, 2)
            
            # Update user's balance
            user.wallet_balance = new_balance
            
            # Create transaction record with the actual amount added to wallet (after fee)
            transaction = Transaction(
                user_id=user.id,
                amount=amount,  # This is already the amount after fee
                description=description,
                status='completed',
                reference_id=f'manual_{int(datetime.utcnow().timestamp())}'
            )
            
            # Add transaction to session
            db_session.add(transaction)
            db_session.add(user)
            
            # Commit the transaction
            db_session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'transaction_id': transaction.id,
                    'amount': amount,
                    'processing_fee': 0.00,
                    'original_amount': amount,
                    'old_balance': old_balance,
                    'new_balance': new_balance,
                    'description': description,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
            
        except Exception as e:
            db_session.rollback()
            current_app.logger.error(f'Error adding to wallet: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'Failed to add to wallet: {str(e)}'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f'Unexpected error in add_to_wallet: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred. Please try again.'
        }), 500
        
    finally:
        # Make sure to close the session
        if 'db_session' in locals():
            db_session.close()

@api_bp.route('/wallet/create-order', methods=['POST'])
@jwt_required()
def create_wallet_order():
    """
    Create a Razorpay order for wallet recharge
    Expected JSON payload:
    {
        "amount": 100.00  // Amount in INR
    }
    """
    try:
        from app import razorpay_client, RAZORPAY_KEY_ID
        
        current_app.logger.info('=== CREATE WALLET ORDER REQUEST ===')
        current_app.logger.info(f'Request Headers: {dict(request.headers)}')
        current_app.logger.info(f'Request Data: {request.get_data()}')
        
        if not razorpay_client:
            error_msg = 'Payment service is currently unavailable. Please try again later.'
            current_app.logger.error(error_msg)
            return jsonify({
                'status': 'error',
                'message': error_msg,
                'code': 'SERVICE_UNAVAILABLE'
            }), 503
            
        data = request.get_json(silent=True)
        user_id = get_jwt_identity()
        
        current_app.logger.info(f'User ID: {user_id}, Parsed Data: {data}')
        
        if not data:
            error_msg = 'No data provided in request body'
            current_app.logger.error(error_msg)
            return jsonify({
                'status': 'error',
                'message': error_msg,
                'code': 'MISSING_DATA'
            }), 400
            
        amount = data.get('amount')
        current_app.logger.info(f'Received amount: {amount} (type: {type(amount).__name__})')
        
        # Validate amount
        try:
            if amount is None:
                raise ValueError('Amount is required')
                
            amount = float(amount)
            current_app.logger.info(f'Parsed amount: {amount}')
            
            # Enforce minimum top-up amount
            MIN_TOPUP_AMOUNT = 1.00
            
            if amount < MIN_TOPUP_AMOUNT:
                error_msg = f'Minimum top-up amount is ₹{MIN_TOPUP_AMOUNT:.2f}'
                current_app.logger.error(f'Validation error: {error_msg}')
                return jsonify({
                    'status': 'error',
                    'message': error_msg,
                    'code': 'INVALID_AMOUNT_MIN',
                    'min_amount': MIN_TOPUP_AMOUNT
                }), 400
                
            if amount > 500:
                error_msg = 'Maximum top-up amount is ₹500'
                current_app.logger.error(f'Validation error: {error_msg}')
                return jsonify({
                    'status': 'error',
                    'message': error_msg,
                    'code': 'INVALID_AMOUNT_MAX',
                    'max_amount': 500
                }), 400
                
            # Log the amount being added
            current_app.logger.info(f'Adding amount to wallet: ₹{amount:.2f}')
            
            if amount <= 0:
                error_msg = 'Amount must be positive'
                current_app.logger.error(f'Validation error: {error_msg}')
                return jsonify({
                    'status': 'error',
                    'message': error_msg,
                    'code': 'INVALID_AMOUNT'
                }), 400
                
        except (TypeError, ValueError) as e:
            error_msg = f'Invalid amount provided: {str(e)}'
            current_app.logger.error(error_msg)
            return jsonify({
                'status': 'error',
                'message': 'Please provide a valid amount',
                'code': 'INVALID_AMOUNT',
                'details': str(e)
            }), 400
        
        # Amount in paise for Razorpay
        amount_in_paise = int(amount * 100)
        receipt_id = f'wlt_{user_id}_{int(datetime.utcnow().timestamp())}'

        # Create order data
        order_data = {
            'amount': amount_in_paise,  # Amount in paise
            'currency': 'INR',
            'receipt': receipt_id,
            'payment_capture': 1,  # Auto-capture payment
            'notes': {
                'description': f'Wallet top-up of ₹{amount:.2f}',
                'user_id': user_id,
                'original_amount': amount
            }
        }
        
        # Create the order
        try:
            razorpay_order = razorpay_client.order.create(data=order_data)
            
            return jsonify({
                'status': 'success',
                'data': {
                    'order_id': razorpay_order['id'],
                    'amount': amount,
                    'currency': 'INR',
                    'key_id': RAZORPAY_KEY_ID,
                    'receipt': receipt_id
                }
            })
            
        except Exception as e:
            current_app.logger.error(f'Error creating Razorpay order: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': 'Failed to create payment order',
                'error': str(e)
            }), 500
            
    except Exception as e:
        current_app.logger.error(f'Unexpected error in create_wallet_order: {str(e)}')
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred. Please try again.'
        }), 500

@api_bp.route('/wallet/deduct-call', methods=['POST'])
@jwt_required()
def deduct_call_charges():
    """
    Direct wallet deduction for call charges (bypasses Razorpay)
    Expected JSON payload:
    {
        "amount": 2.5,
        "call_id": "call_xyz",
        "callee_id": 8  # User receiving the payment
    }
    """
    current_user_id = int(get_jwt_identity())
    
    current_app.logger.info(f"[CALL_DEDUCT] Request from user {current_user_id}")
    
    try:
        data = request.get_json()
        current_app.logger.info(f"[CALL_DEDUCT] Request data: {data}")
        
        if not data or 'amount' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Amount is required'
            }), 400
        
        amount = float(data['amount'])
        callee_id = data.get('callee_id')
        call_id = data.get('call_id', f'call_{int(datetime.utcnow().timestamp())}')
        
        # Get caller (current user)
        caller = User.query.get(current_user_id)
        if not caller:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        caller_balance = float(caller.wallet_balance) if caller.wallet_balance else 0.0
        
        # Check sufficient balance
        if caller_balance < amount:
            return jsonify({
                'status': 'error',
                'message': 'Insufficient wallet balance',
                'current_balance': caller_balance,
                'required_amount': amount
            }), 400
        
        # Deduct from caller
        caller.wallet_balance = round(caller_balance - amount, 2)
        
        # Create deduction transaction
        deduction_tx = Transaction(
            user_id=current_user_id,
            amount=-amount,
            transaction_type='debit',
            status='completed',
            description=f'Call charge: ₹{amount}',
            reference_id=call_id,
            metadata={'type': 'call_charge', 'call_id': call_id}
        )
        db.session.add(deduction_tx)
        
        # Add to callee if provided
        if callee_id:
            callee = User.query.get(callee_id)
            if callee:
                earning = round(amount * 0.8, 2)  # 80% to callee
                callee_balance = float(callee.wallet_balance) if callee.wallet_balance else 0.0
                callee.wallet_balance = round(callee_balance + earning, 2)
                
                # Create earning transaction
                earning_tx = Transaction(
                    user_id=callee_id,
                    amount=earning,
                    transaction_type='credit',
                    status='completed',
                    description=f'Call earning: ₹{earning}',
                    reference_id=call_id,
                    metadata={'type': 'call_earning', 'call_id': call_id}
                )
                db.session.add(earning_tx)
        
        db.session.commit()
        
        current_app.logger.info(f"[CALL_DEDUCT] Deducted ₹{amount} from user {current_user_id}")
        
        return jsonify({
            'status': 'success',
            'message': f'Deducted ₹{amount} from wallet',
            'wallet': {
                'balance': caller.wallet_balance,
                'deducted_amount': amount,
                'transaction_id': deduction_tx.id
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"[CALL_DEDUCT] Error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to process deduction'
        }), 500

@api_bp.route('/portfolio', methods=['GET', 'POST', 'PUT'])
@jwt_required(optional=True)
def manage_portfolio():
    """
    Get, create or update the authenticated user's portfolio
    """
    if request.method == 'GET':
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
            
        portfolio = PortfolioModel.query.filter_by(user_id=user_id).first()
        if not portfolio:
            return jsonify({'status': 'not_found', 'message': 'Portfolio not found'}), 404
            
        return get_portfolio_response(portfolio)
        
    elif request.method in ['POST', 'PUT']:
        # Create or update portfolio
        data = request.get_json()
        
        portfolio = PortfolioModel.query.filter_by(user_id=user_id).first()
        if not portfolio and request.method == 'PUT':
            return jsonify({
                'status': 'not_found',
                'message': 'Portfolio not found. Use POST to create.'
            }), 404
            
        if not portfolio:
            portfolio = PortfolioModel(user_id=user_id)
            db.session.add(portfolio)
            
        # Update fields
        if 'description' in data:
            portfolio.description = data['description']
        if 'skills' in data and isinstance(data['skills'], list):
            portfolio.skills = ', '.join([s.strip() for s in data['skills'] if s.strip()])
        if 'experience' in data:
            portfolio.experience = data['experience']
            
        portfolio.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Portfolio updated successfully' if request.method == 'PUT' else 'Portfolio created successfully',
            'portfolio': {
                'id': portfolio.id,
                'user_id': portfolio.user_id,
                'description': portfolio.description,
                'skills': get_skills_list(portfolio.skills),
                'experience': portfolio.experience,
                'created_at': portfolio.created_at.isoformat() if portfolio.created_at else None,
                'updated_at': portfolio.updated_at.isoformat() if portfolio.updated_at else None
            }
        }), 200 if request.method == 'PUT' else 201

@api_bp.route('/users/<int:user_id>/portfolio', methods=['GET'])
def get_user_portfolio(user_id):
    """
    Get a user's portfolio by user ID
    """
    portfolio = PortfolioModel.query.filter_by(user_id=user_id).first()
    if not portfolio:
        return jsonify({'status': 'not_found', 'message': 'Portfolio not found'}), 404
        
    return get_portfolio_response(portfolio)

@api_bp.route('/users/<int:user_id>/reviews', methods=['GET'])
def get_user_reviews(user_id):
    """
    Get paginated reviews for a user
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        # Get reviews with reviewer info
        reviews_query = db.session.query(
            Review,
            User.full_name,
            User.photo
        ).join(
            User, User.id == Review.reviewer_id
        ).filter(
            Review.worker_id == user_id
        ).order_by(Review.created_at.desc())
        
        pagination = reviews_query.paginate(page=page, per_page=per_page, error_out=False)
        reviews = pagination.items
        
        # Calculate average rating
        avg_rating = db.session.query(func.avg(Review.rating))\
            .filter(Review.worker_id == user_id)\
            .scalar() or 0
        
        # Format response
        reviews_data = []
        for review, reviewer_name, reviewer_photo in reviews:
            reviews_data.append({
                'id': review.id,
                'reviewer_name': reviewer_name,
                'reviewer_photo': url_for('serve_profile_pic', filename=reviewer_photo, _external=True) if reviewer_photo else url_for('static', filename='img/default-avatar.png', _external=True),
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.isoformat() if review.created_at else None,
            })
            
        return jsonify({
            'total_reviews': pagination.total,
            'average_rating': float(round(avg_rating, 1)) if avg_rating else 0,
            'page': page,
            'per_page': per_page,
            'reviews': reviews_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching user reviews: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch reviews',
            'error': str(e)
        }), 500

@api_bp.route('/reviews', methods=['POST'])
@jwt_required()
def create_review():
    """
    Submit a review for a user
    Expected JSON payload:
    {
        "user_id": 123,
        "rating": 5,
        "comment": "Great service!",
        "anonymous": false
    }
    """
    try:
        current_app.logger.info(f'Received review request: {request.get_data()}')
        
        data = request.get_json()
        if not data:
            current_app.logger.error('No JSON data received')
            return jsonify({
                'status': 'error',
                'message': 'No data provided',
                'details': 'Request body must be a valid JSON'
            }), 400
        
        current_app.logger.info(f'Parsed JSON data: {data}')
        
        # Validate required fields
        required_fields = ['user_id', 'rating']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            current_app.logger.error(f'Missing required fields: {missing_fields}')
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields',
                'missing_fields': missing_fields,
                'received_data': data
            }), 400
        
        # Get reviewer ID from JWT
        try:
            reviewer_id = get_jwt_identity()
            current_app.logger.info(f'Reviewer ID from JWT: {reviewer_id}')
            
            # Check if user is reviewing themselves
            if reviewer_id == data['user_id']:
                current_app.logger.error('User attempted to review themselves')
                return jsonify({
                    'status': 'error',
                    'message': 'You cannot review yourself',
                    'details': 'Reviewer ID and target user ID are the same'
                }), 400
                
            # Validate user_id exists
            target_user = User.query.get(data['user_id'])
            if not target_user:
                current_app.logger.error(f'Target user not found: {data["user_id"]}')
                return jsonify({
                    'status': 'error',
                    'message': 'User not found',
                    'details': f'No user found with ID: {data["user_id"]}'
                }), 404
                
        except Exception as e:
            current_app.logger.error(f'Error processing JWT or user validation: {str(e)}')
            return jsonify({
                'status': 'error',
                'message': 'Authentication error',
                'details': str(e)
            }), 401
            
        # Check if review already exists
        existing_review = Review.query.filter_by(
            reviewer_id=reviewer_id,
            worker_id=data['user_id']
        ).first()
        
        if existing_review:
            return jsonify({
                'status': 'error',
                'message': 'You have already reviewed this user'
            }), 400
            
        # Validate rating
        rating = int(data['rating'])
        if rating < 1 or rating > 5:
            return jsonify({
                'status': 'error',
                'message': 'Rating must be between 1 and 5'
            }), 400
            
        # Create new review
        review = Review(
            reviewer_id=reviewer_id,
            worker_id=data['user_id'],
            rating=rating,
            comment=data.get('comment', '')
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Update user's average rating
        update_user_rating(data['user_id'])
        
        return jsonify({
            'status': 'success',
            'message': 'Review submitted successfully',
            'review': {
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.isoformat() if review.created_at else None,
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating review: {str(e)}", exc_info=True)
        current_app.logger.error(f"Request data: {data}")
        
        # Check if this is a database integrity error
        error_message = 'Failed to submit review'
        error_details = str(e)
        
        if 'UNIQUE constraint failed' in str(e):
            error_message = 'You have already reviewed this user'
            error_details = 'Duplicate review detected'
        elif 'FOREIGN KEY constraint failed' in str(e):
            error_message = 'Invalid user reference'
            error_details = 'The user being reviewed does not exist'
            
        return jsonify({
            'status': 'error',
            'message': error_message,
            'details': error_details,
            'message': 'Failed to submit review',
            'error': str(e)
        }), 500

def update_user_rating(user_id):
    """Update user's average rating"""
    try:
        # Calculate new average rating
        result = db.session.query(
            func.avg(Review.rating).label('average_rating'),
            func.count(Review.id).label('review_count')
        ).filter(
            Review.worker_id == user_id
        ).first()
        
        if result and result.average_rating:
            user = User.query.get(user_id)
            if user:
                user.rating = round(float(result.average_rating), 1)
                user.review_count = result.review_count
                db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user rating: {str(e)}")
        raise

# ==============================================
# Job Posting Endpoints
# ==============================================

@api_bp.route('/jobs', methods=['POST'])
@jwt_required()
def create_job_posting():
    """
    Create a new job posting
    Expected JSON payload:
    {
        "title": "Website Development",
        "description": "Need a professional website for my business",
        "category": "web_development",
        "budget": 1000.00,
        "budget_type": "fixed",  # or "hourly"
        "location": "New York, NY",
        "address": "123 Business St, New York, NY 10001",
        "duration": "2 weeks",
        "skills_required": ["HTML", "CSS", "JavaScript"],
        "contact_phone": "+1234567890",
        "contact_email": "client@example.com"
    }
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Log incoming request details
        current_app.logger.info(f"[JOB_POST] Incoming request headers: {dict(request.headers)}")
        current_app.logger.info(f"[JOB_POST] Request content type: {request.content_type}")
        
        # Get request data based on content type
        if 'application/json' in request.content_type:
            try:
                # Try to parse JSON data
                data = request.get_json(force=True, silent=True)
                if data is None:
                    # If get_json returns None, try to parse manually
                    raw_data = request.get_data(as_text=True)
                    if raw_data:
                        data = json.loads(raw_data)
                current_app.logger.info(f"[JOB_POST] Received JSON data: {data}")
            except Exception as e:
                current_app.logger.error(f"[JOB_POST] Error parsing JSON data: {str(e)}")
                data = {}
        else:
            data = request.form.to_dict()
            current_app.logger.info(f"[JOB_POST] Received form data: {data}")
        
        # If no data was found, try to parse it manually
        if not data and request.method == 'POST':
            try:
                data = json.loads(request.get_data(as_text=True))
                current_app.logger.info(f"[JOB_POST] Manually parsed JSON data: {data}")
            except Exception as e:
                current_app.logger.error(f"[JOB_POST] Error parsing request data: {str(e)}")
                data = {}
        
        # Check if data contains a 'job' field with JSON string
        if data and 'job' in data and isinstance(data['job'], str):
            try:
                data = json.loads(data['job'])
                current_app.logger.info(f"[JOB_POST] Parsed job data from 'job' field: {data}")
            except json.JSONDecodeError as e:
                current_app.logger.error(f"[JOB_POST] Error parsing 'job' field as JSON: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid JSON data in job field'
                }), 400
        
        current_app.logger.info(f"[JOB_POST] Final data being processed: {data}")
        
        # If still no data, return error
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Invalid request data. Please send valid JSON data with the required fields.'
            }), 400
        
        # Validate required fields
        required_fields = ['title', 'description', 'category', 'budget', 'budget_type', 'location']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Get coordinates from location
        coordinates = get_coordinates(data['location'])
        if not coordinates:
            return jsonify({
                'status': 'error',
                'message': 'Could not determine location coordinates. Please provide a valid location.'
            }), 400
            
        latitude, longitude = coordinates
        
        # Handle image uploads
        image_urls = []
        if request.files:
            current_app.logger.info(f"[JOB_POST] Processing {len(request.files)} file(s)")
            
            # Ensure upload directory exists
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'job_images')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Process each uploaded file
            for file_key in request.files:
                file = request.files[file_key]
                
                # Skip if no filename
                if not file or not file.filename or file.filename == '':
                    current_app.logger.warning(f"[JOB_POST] Skipping empty file in field: {file_key}")
                    continue
                
                current_app.logger.info(f"[JOB_POST] Processing file: {file.filename} from field: {file_key}")
                
                # Validate file size by reading the stream
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size <= 0:
                    current_app.logger.warning(f"[JOB_POST] Empty file detected: {file.filename}")
                    continue
                
                current_app.logger.info(f"[JOB_POST] File size: {file_size} bytes")
                
                # Validate file type by checking file signature (magic bytes)
                file_header = file.read(10)
                file.seek(0)  # Reset to beginning
                
                # Check for common image file signatures
                is_valid_image = (
                    file_header.startswith(b'\x89PNG') or  # PNG
                    file_header.startswith(b'\xff\xd8\xff') or  # JPEG
                    file_header.startswith(b'GIF87a') or  # GIF87a
                    file_header.startswith(b'GIF89a') or  # GIF89a
                    file_header.startswith(b'RIFF') and b'WEBP' in file_header  # WebP
                )
                
                if not is_valid_image:
                    current_app.logger.warning(f"[JOB_POST] Invalid image file signature for: {file.filename}")
                    continue
                
                # Generate unique filename
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                
                # Determine extension from file signature if not present or incorrect
                if not ext or ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
                    if file_header.startswith(b'\x89PNG'):
                        ext = 'png'
                    elif file_header.startswith(b'\xff\xd8\xff'):
                        ext = 'jpg'
                    elif file_header.startswith(b'GIF'):
                        ext = 'gif'
                    elif b'WEBP' in file_header:
                        ext = 'webp'
                    else:
                        ext = 'jpg'  # Default fallback
                
                new_filename = f"{uuid.uuid4()}.{ext}"
                file_path = os.path.join(upload_dir, new_filename)
                
                # Save file
                file.save(file_path)
                current_app.logger.info(f"[JOB_POST] Saved image: {new_filename}")
                
                # Build full URL for the image
                # Using request.host_url to get the full base URL (e.g., http://192.168.1.100:5000/)
                base_url = request.host_url.rstrip('/')
                image_url = f"{base_url}/static/uploads/job_images/{new_filename}"
                image_urls.append(image_url)
                current_app.logger.info(f"[JOB_POST] Generated image URL: {image_url}")
        
        current_app.logger.info(f"[JOB_POST] Total images saved: {len(image_urls)}")
        current_app.logger.info(f"[JOB_POST] Image URLs to save: {image_urls}")
        
        # Create new job posting
        job = JobPosting(
            title=data['title'],
            description=data['description'],
            category=data['category'],
            budget=float(data['budget']),
            budget_type=data['budget_type'],
            location=data['location'],
            address=data.get('address', ''),
            latitude=latitude,
            longitude=longitude,
            duration=data.get('duration', ''),
            skills_required=data.get('skills_required', []),
            contact_phone=data.get('contact_phone', ''),
            contact_email=data.get('contact_email', ''),
            client_id=current_user_id,
            status='open',
            images=image_urls
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Refresh to get the saved data
        db.session.refresh(job)
        current_app.logger.info(f"[JOB_POST] Job created with ID: {job.id}")
        current_app.logger.info(f"[JOB_POST] Job images field after save: {job.images}")
        
        job_dict = job.to_dict()
        current_app.logger.info(f"[JOB_POST] Job dict images: {job_dict.get('images')}")
        
        return jsonify({
            'status': 'success',
            'message': 'Job posted successfully',
            'job': job_dict
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating job posting: {str(e)}', exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while creating the job posting',
            'error': str(e)
        }), 500

@api_bp.route('/jobs', methods=['GET'])
def get_job_postings():
    """
    Get all job postings with filtering and pagination
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    - category: Filter by category
    - budget_min: Minimum budget
    - budget_max: Maximum budget
    - location: Filter by location (within 50km if coordinates available)
    - search: Search in title or description
    - status: Filter by status (open, in_progress, completed, cancelled)
    - sort: Sort by (newest, budget_high, budget_low)
    """
    try:
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Base query
        query = JobPosting.query
        
        # Apply filters
        if 'category' in request.args:
            query = query.filter(JobPosting.category == request.args['category'])
            
        if 'budget_min' in request.args:
            query = query.filter(JobPosting.budget >= float(request.args['budget_min']))
            
        if 'budget_max' in request.args:
            query = query.filter(JobPosting.budget <= float(request.args['budget_max']))
            
        if 'status' in request.args:
            query = query.filter(JobPosting.status == request.args['status'])
        else:
            # Default to only showing open jobs
            query = query.filter(JobPosting.status == 'open')
            
        if 'search' in request.args:
            search = f"%{request.args['search']}%"
            query = query.filter(
                or_(
                    JobPosting.title.ilike(search),
                    JobPosting.description.ilike(search)
                )
            )
            
        # Location-based filtering
        if 'location' in request.args:
            location = request.args['location']
            coordinates = get_coordinates(location)
            if coordinates:
                lat, lng = coordinates
                # This is a simplified approach - in production, you'd want to use PostGIS for spatial queries
                # For now, we'll just filter by location text match
                query = query.filter(JobPosting.location.ilike(f'%{location}%'))
        
        # Sorting
        sort = request.args.get('sort', 'newest')
        if sort == 'budget_high':
            query = query.order_by(JobPosting.budget.desc())
        elif sort == 'budget_low':
            query = query.order_by(JobPosting.budget.asc())
        else:  # newest first by default
            query = query.order_by(JobPosting.created_at.desc())
        
        # Execute query with pagination
        paginated_jobs = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Prepare response
        jobs = [job.to_dict() for job in paginated_jobs.items]
        
        return jsonify({
            'status': 'success',
            'data': jobs,
            'pagination': {
                'total': paginated_jobs.total,
                'pages': paginated_jobs.pages,
                'current_page': paginated_jobs.page,
                'per_page': paginated_jobs.per_page,
                'has_next': paginated_jobs.has_next,
                'has_prev': paginated_jobs.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching job postings: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching job postings',
            'error': str(e)
        }), 500

@api_bp.route('/jobs/<int:job_id>', methods=['GET'])
def get_job_posting(job_id):
    """Get details of a specific job posting"""
    try:
        job = JobPosting.query.get_or_404(job_id)
        return jsonify({
            'status': 'success',
            'data': job.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f'Error fetching job posting {job_id}: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching the job posting',
            'error': str(e)
        }), 500

@api_bp.route('/jobs/<int:job_id>', methods=['PUT'])
@jwt_required()
def update_job_posting(job_id):
    """
    Update a job posting
    Only the job poster or admin can update the job
    """
    try:
        current_user_id = get_jwt_identity()
        job = JobPosting.query.get_or_404(job_id)
        
        # Check permissions
        if job.client_id != current_user_id:
            # Check if user is admin
            user = User.query.get(current_user_id)
            if not user or not user.is_admin:
                return jsonify({
                    'status': 'error',
                    'message': 'You do not have permission to update this job posting'
                }), 403
        
        data = request.get_json()
        
        # Update fields if provided
        for field in ['title', 'description', 'category', 'budget', 'budget_type', 
                     'location', 'address', 'duration', 'status']:
            if field in data:
                setattr(job, field, data[field])
        
        # Update skills if provided
        if 'skills_required' in data:
            job.skills_required = data['skills_required']
            
        # Update contact info if provided
        if 'contact_phone' in data:
            job.contact_phone = data['contact_phone']
        if 'contact_email' in data:
            job.contact_email = data['contact_email']
        
        # If location changed, update coordinates
        if 'location' in data:
            coordinates = get_coordinates(data['location'])
            if coordinates:
                job.latitude, job.longitude = coordinates
        
        job.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Job posting updated successfully',
            'data': job.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating job posting {job_id}: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating the job posting',
            'error': str(e)
        }), 500

@api_bp.route('/jobs/<int:job_id>', methods=['DELETE'])
@jwt_required()
def delete_job_posting(job_id):
    """
    Delete a job posting
    Only the job poster or admin can delete the job
    """
    try:
        current_user_id = get_jwt_identity()
        job = JobPosting.query.get_or_404(job_id)
        
        # Check permissions
        if job.client_id != current_user_id:
            # Check if user is admin
            user = User.query.get(current_user_id)
            if not user or not user.is_admin:
                return jsonify({
                    'status': 'error',
                    'message': 'You do not have permission to delete this job posting'
                }), 403
        
        # Soft delete by changing status
        job.status = 'cancelled'
        job.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Job posting deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting job posting {job_id}: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while deleting the job posting',
            'error': str(e)
        }), 500

@api_bp.route('/jobs/<int:job_id>/requests', methods=['GET'])
@jwt_required()
def get_job_requests(job_id):
    """
    Get all job requests for a specific job posting
    """
    try:
        current_user_id = get_jwt_identity()
        job = JobPosting.query.get_or_404(job_id)
        
        # Only the job poster can view requests
        if job.client_id != current_user_id:
            return jsonify({
                'status': 'error',
                'message': 'You are not authorized to view requests for this job'
            }), 403
        
        # Get all requests for this job
        requests = JobRequest.query.filter_by(job_id=job_id).order_by(JobRequest.created_at.desc()).all()
        
        return jsonify({
            'status': 'success',
            'requests': [req.to_dict() for req in requests]
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching job requests for job {job_id}: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching job requests',
            'error': str(e)
        }), 500

@api_bp.route('/jobs/<int:job_id>/apply', methods=['POST'])
@jwt_required()
def apply_for_job(job_id):
    """
    Apply for a job posting
    """
    try:
        current_user_id = get_jwt_identity()
        job = JobPosting.query.get_or_404(job_id)
        
        # Check if job is open
        if job.status != 'open':
            return jsonify({
                'status': 'error',
                'message': 'This job is no longer accepting applications'
            }), 400
        
        # Check if user is the job poster
        if job.client_id == current_user_id:
            return jsonify({
                'status': 'error',
                'message': 'You cannot apply to your own job posting'
            }), 400
        
        # Check if user has already applied
        existing_request = JobRequest.query.filter_by(
            job_id=job_id,
            worker_id=current_user_id
        ).first()
        
        if existing_request:
            return jsonify({
                'status': 'error',
                'message': 'You have already applied to this job',
                'request': existing_request.to_dict()
            }), 400
        
        # Create job request
        data = request.get_json() or {}
        job_request = JobRequest(
            job_id=job_id,
            worker_id=current_user_id,
            client_id=job.client_id,
            status='pending',
            message=data.get('message', '')
        )
        
        db.session.add(job_request)
        db.session.commit()
        
        # Send notification to job poster
        # notification_service.send_job_application_notification(
        #     job.client_id,
        #     f'New application for your job: {job.title}',
        #     f'{current_user.full_name} has applied to your job posting.',
        #     {'type': 'job_application', 'job_id': job.id, 'applicant_id': current_user_id}
        # )
        
        return jsonify({
            'status': 'success',
            'message': 'Application submitted successfully',
            'job': job.to_dict(),
            'request': job_request.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f'Error applying for job {job_id}: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while processing your application',
            'error': str(e)
        }), 500

def _update_job_request_status(request_id, data, current_user_id):
    """
    Internal function to update job request status
    
    Args:
        request_id: ID of the job request
        data: Dictionary containing status and optional rejection_reason
        current_user_id: ID of the user making the request
        
    Returns:
        Tuple of (response_data, status_code)
    """
    if not data or 'status' not in data:
        return {
            'success': False,
            'message': 'Missing required field: status'
        }, 400
        
    new_status = data['status'].lower()
    
    # Validate status
    valid_statuses = ['accepted', 'rejected', 'cancelled']
    if new_status not in valid_statuses:
        return {
            'success': False,
            'message': f'Invalid status. Must be one of: {valid_statuses}'
        }, 400
        
    # Check if rejection reason is provided when rejecting
    if new_status == 'rejected' and not data.get('rejection_reason'):
        return {
            'success': False,
            'message': 'Rejection reason is required when rejecting a request'
        }, 400
        
    # Get the job request
    job_request = JobRequest.query.get(request_id)
    if not job_request:
        return {
            'success': False,
            'message': f'Job request with ID {request_id} not found'
        }, 404
    
    # Ensure current_user_id is an integer for comparison
    current_user_id = int(current_user_id) if isinstance(current_user_id, str) else current_user_id
    
    # Debug logging
    current_app.logger.info(
        f'Job request {request_id}: worker_id={job_request.worker_id} (type: {type(job_request.worker_id).__name__}), '
        f'client_id={job_request.client_id} (type: {type(job_request.client_id).__name__}), '
        f'status={job_request.status}, '
        f'current_user={current_user_id} (type: {type(current_user_id).__name__}), '
        f'new_status={new_status}'
    )
    
    # Check permissions
    if new_status == 'cancelled':
        # Only the worker who created the request can cancel it
        if job_request.worker_id != current_user_id:
            current_app.logger.warning(
                f'Authorization failed: User {current_user_id} tried to cancel request {request_id} '
                f'but worker_id is {job_request.worker_id}'
            )
            return {
                'success': False,
                'message': 'You are not authorized to cancel this request. Only the worker who applied can cancel.'
            }, 403
    else:
        # Only the client who posted the job can accept/reject requests
        if job_request.client_id != current_user_id:
            current_app.logger.warning(
                f'Authorization failed: User {current_user_id} tried to {new_status} request {request_id} '
                f'but client_id is {job_request.client_id}'
            )
            return {
                'success': False,
                'message': f'You are not authorized to {new_status} this request. Only the job poster can accept/reject applications.'
            }, 403
    
    # Update the status
    job_request.status = new_status
    
    # Update rejection reason if provided
    if new_status == 'rejected' and 'rejection_reason' in data:
        job_request.rejection_reason = data['rejection_reason']
    
    # If request is accepted, mark the job as in_progress
    if new_status == 'accepted':
        job_request.job.status = 'in_progress'
        job_request.job.assigned_to = job_request.worker_id
    
    db.session.commit()
    
    return {
        'success': True,
        'message': 'Job request updated successfully',
        'request': job_request.to_dict()
    }, 200

@api_bp.route('/job-requests/sent', methods=['GET'])
@jwt_required()
def get_sent_job_requests():
    """
    Get all job requests sent by the current user (worker applications)
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get all requests where the current user is the worker
        requests = JobRequest.query.filter_by(worker_id=current_user_id).order_by(JobRequest.created_at.desc()).all()
        
        # Include job details in the response
        result = []
        for req in requests:
            req_dict = req.to_dict()
            if req.job:
                req_dict['job'] = req.job.to_dict()
            result.append(req_dict)
        
        return jsonify({
            'status': 'success',
            'requests': result
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching sent job requests: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching job requests',
            'error': str(e)
        }), 500

@api_bp.route('/job-requests/received', methods=['GET'])
@jwt_required()
def get_received_job_requests():
    """
    Get all job requests received by the current user (client's job postings)
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get all requests where the current user is the client
        requests = JobRequest.query.filter_by(client_id=current_user_id).order_by(JobRequest.created_at.desc()).all()
        
        # Include job and worker details in the response
        result = []
        for req in requests:
            req_dict = req.to_dict()
            if req.job:
                req_dict['job'] = req.job.to_dict()
            if req.worker:
                req_dict['worker'] = {
                    'id': req.worker.id,
                    'full_name': req.worker.full_name,
                    'username': req.worker.username,
                    'profile_pic': req.worker.get_profile_pic_url() if hasattr(req.worker, 'get_profile_pic_url') else None
                }
            result.append(req_dict)
        
        return jsonify({
            'status': 'success',
            'requests': result
        })
        
    except Exception as e:
        current_app.logger.error(f'Error fetching received job requests: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching job requests',
            'error': str(e)
        }), 500

@api_bp.route('/job-requests/status', methods=['POST'])
@jwt_required()
def update_job_request_status():
    """
    Update the status of a job request (legacy endpoint)
    
    Expected JSON payload:
    {
        "request_id": 123,            # ID of the job request
        "status": "accepted",         # New status: 'accepted', 'rejected', or 'cancelled'
        "rejection_reason": "..."     # Required if status is 'rejected'
    }
    
    Returns:
        JSON response with the updated request or error message
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data or 'request_id' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required field: request_id'
            }), 400
            
        return jsonify(_update_job_request_status(data['request_id'], data, current_user_id)[0]), 200
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating job request status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating the job request',
            'error': str(e)
        }), 500

@api_bp.route('/job-requests/<int:request_id>/status', methods=['PUT'])
@jwt_required()
def update_job_request_status_restful(request_id):
    """
    Update the status of a job request (RESTful endpoint)
    
    Expected JSON payload:
    {
        "status": "accepted",         # New status: 'accepted', 'rejected', or 'cancelled'
        "rejection_reason": "..."     # Required if status is 'rejected'
    }
    
    Returns:
        JSON response with the updated request or error message
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Debug logging
        current_app.logger.info(f"Update request - User: {current_user_id}, Request ID: {request_id}, Data: {data}")
        
        response_data, status_code = _update_job_request_status(request_id, data, current_user_id)
        return jsonify(response_data), status_code
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating job request status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating the job request',
            'error': str(e)
        }), 500

# ==============================================
# Account Management Endpoints
# ==============================================

@api_bp.route('/account', methods=['GET'])
@jwt_required()
def get_account():
    """
    Get current user's account information
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': {
                'id': user.id,
                'email': user.email,
                'username': user.username if hasattr(user, 'username') else None,
                'full_name': user.full_name,
                'phone': user.phone,
                'user_type': user.user_type,
                'profile_photo': url_for('serve_profile_pic', filename=user.photo, _external=True) if hasattr(user, 'photo') and user.photo else url_for('static', filename='img/default-avatar.png', _external=True),
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None,
                'is_active': user.active,
                'address': user.address if hasattr(user, 'address') else None,
                'bio': user.bio if hasattr(user, 'bio') else None,
                'date_of_birth': user.date_of_birth.isoformat() if hasattr(user, 'date_of_birth') and user.date_of_birth else None,
                'gender': user.gender if hasattr(user, 'gender') else None,
                'rating': user.rating if hasattr(user, 'rating') else None,
                'review_count': user.review_count if hasattr(user, 'review_count') else 0
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting account: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching account information'
        }), 500

@api_bp.route('/account', methods=['PUT', 'PATCH'])
@jwt_required()
def update_account():
    """
    Update current user's account information
    Supports both PUT (full update) and PATCH (partial update) methods
    
    Expected JSON payload (all fields optional):
    {
        "email": "new@example.com",
        "full_name": "New Name",
        "phone": "+1234567890",
        "bio": "Updated bio",
        "address": "123 New Street, City",
        "date_of_birth": "1990-01-01",
        "gender": "male/female/other/prefer_not_to_say",
        "profession": "Software Developer",
        "experience": "5 years",
        "education": "Bachelor's in Computer Science",
        "skills": "Python, JavaScript, Flutter",
        "payment_rate": 50.0,
        "payment_type": "hourly"
    }
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
            
        data = request.get_json()
        
        # Update fields if provided
        if 'email' in data and data['email'] != user.email:
            if not validate_email(data['email']):
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid email format'
                }), 400
                
            if User.query.filter(User.email == data['email'], User.id != user.id).first():
                return jsonify({
                    'status': 'error',
                    'message': 'Email already in use by another account'
                }), 409
            user.email = data['email']
            
        if 'full_name' in data:
            user.full_name = data['full_name']
            
        if 'phone' in data and data['phone'] != user.phone:
            if User.query.filter(User.phone == data['phone'], User.id != user.id).first():
                return jsonify({
                    'status': 'error',
                    'message': 'Phone number already in use by another account'
                }), 409
            user.phone = data['phone']
            
        # Update optional fields
        if 'bio' in data and hasattr(user, 'bio'):
            user.bio = data['bio']
            
        # Update location if provided
        if 'location' in data and data['location']:
            try:
                location_str = data['location']
                coordinates = get_coordinates(location_str)
                
                if coordinates:
                    user.current_location = location_str
                    user.live_location = f"{coordinates[0]},{coordinates[1]}"
                    current_app.logger.info(f"Updated location for user {user_id}: {location_str} ({coordinates[0]}, {coordinates[1]})")
                else:
                    current_app.logger.warning(f"Could not geocode location: {location_str}")
                    # Optionally, you could return an error here if geocoding is required
                    # return jsonify({
                    #     'status': 'error',
                    #     'message': 'Could not find coordinates for the provided location'
                    # }), 400
            except Exception as e:
                current_app.logger.error(f"Error updating location: {str(e)}")
                # Continue without failing the entire update
                
        # Update optional fields
        if 'address' in data and hasattr(user, 'address'):
            user.address = data['address']
            
        if 'date_of_birth' in data and hasattr(user, 'date_of_birth'):
            try:
                user.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
                
        if 'gender' in data and hasattr(user, 'gender') and data['gender'] in ['male', 'female', 'other', 'prefer_not_to_say']:
            user.gender = data['gender']
            
        # Update additional profile fields
        if 'profession' in data and hasattr(user, 'profession'):
            user.profession = data['profession']
            
        if 'experience' in data and hasattr(user, 'experience'):
            user.experience = data['experience']
            
        if 'education' in data and hasattr(user, 'education'):
            user.education = data['education']
            
        if 'skills' in data and hasattr(user, 'skills'):
            user.skills = data['skills']
            
        if 'payment_rate' in data and hasattr(user, 'payment_charge'):
            try:
                user.payment_charge = float(data['payment_rate']) if data['payment_rate'] is not None else None
            except (ValueError, TypeError):
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid payment rate format. Must be a number.'
                }), 400
                
        if 'payment_type' in data and hasattr(user, 'payment_type') and data['payment_type'] in ['hourly', 'daily', 'monthly', 'fixed']:
            user.payment_type = data['payment_type']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Account updated successfully',
            'data': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'phone': user.phone,
                'bio': getattr(user, 'bio', None),
                'address': getattr(user, 'address', None),
                'date_of_birth': user.date_of_birth.isoformat() if hasattr(user, 'date_of_birth') and user.date_of_birth else None,
                'gender': getattr(user, 'gender', None),
                'profession': getattr(user, 'profession', None),
                'experience': getattr(user, 'experience', None),
                'education': getattr(user, 'education', None),
                'skills': getattr(user, 'skills', None),
                'payment_rate': float(user.payment_charge) if hasattr(user, 'payment_charge') and user.payment_charge is not None else None,
                'payment_charge': float(user.payment_charge) if hasattr(user, 'payment_charge') and user.payment_charge is not None else None,
                'payment_type': getattr(user, 'payment_type', 'hourly'),
'location': getattr(user, 'current_location', ''),
                'current_location': getattr(user, 'current_location', ''),
                'live_location': getattr(user, 'live_location', ''),
                'latitude': float(user.live_location.split(',')[0]) if user.live_location and ',' in user.live_location else None,
                'longitude': float(user.live_location.split(',')[1]) if user.live_location and ',' in user.live_location else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating account: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating account information'
        }), 500

@api_bp.route('/account/password', methods=['PUT'])
@jwt_required()
def change_password():
    """
    Change current user's password
    Expected JSON payload:
    {
        "current_password": "oldpassword123",
        "new_password": "NewSecurePass123!"
    }
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
            
        data = request.get_json()
        
        # Validate required fields
        if 'current_password' not in data or 'new_password' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Current password and new password are required'
            }), 400
            
        # Verify current password
        if not user.check_password(data['current_password']):
            return jsonify({
                'status': 'error',
                'message': 'Current password is incorrect'
            }), 401
            
        # Validate new password
        is_valid, message = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
            
        # Check if new password is same as old password
        if user.check_password(data['new_password']):
            return jsonify({
                'status': 'error',
                'message': 'New password cannot be the same as current password'
            }), 400
            
        # Update password
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Password updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error changing password: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while changing password'
        }), 500

@api_bp.route('/account/deactivate', methods=['POST'])
@jwt_required()
def deactivate_account():
    """
    Deactivate current user's account (soft delete)
    Expected JSON payload (optional):
    {
        "password": "userpassword123"
    }
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
            
        # If password is provided, verify it
        data = request.get_json() or {}
        if 'password' in data and not user.check_password(data['password']):
            return jsonify({
                'status': 'error',
                'message': 'Incorrect password'
            }), 401
            
        # Deactivate the account (soft delete)
        user.active = False
        if hasattr(user, 'deactivated_at'):
            user.deactivated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Account deactivated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deactivating account: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while deactivating the account'
        }), 500

@api_bp.route('/account/notifications', methods=['GET'])
@jwt_required()
def get_notification_preferences():
    """
    Get current user's notification preferences
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': {
                'email_notifications': user.email_notifications if hasattr(user, 'email_notifications') else True,
                'push_notifications': user.push_notifications if hasattr(user, 'push_notifications') else True,
                'sms_notifications': user.sms_notifications if hasattr(user, 'sms_notifications') else False,
                'marketing_emails': user.marketing_emails if hasattr(user, 'marketing_emails') else False,
                'notification_sound': user.notification_sound if hasattr(user, 'notification_sound') else True,
                'vibrate': user.vibrate if hasattr(user, 'vibrate') else True
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting notification preferences: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching notification preferences'
        }), 500

@api_bp.route('/account/notifications', methods=['PUT'])
@jwt_required()
def update_notification_preferences():
    """
    Update current user's notification preferences
    Expected JSON payload (all fields optional):
    {
        "email_notifications": true,
        "push_notifications": true,
        "sms_notifications": false,
        "marketing_emails": false,
        "notification_sound": true,
        "vibrate": true
    }
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
            
        data = request.get_json()
        
        # Update notification preferences if the attributes exist on the user model
        if 'email_notifications' in data and isinstance(data['email_notifications'], bool) and hasattr(user, 'email_notifications'):
            user.email_notifications = data['email_notifications']
            
        if 'push_notifications' in data and isinstance(data['push_notifications'], bool) and hasattr(user, 'push_notifications'):
            user.push_notifications = data['push_notifications']
            
        if 'sms_notifications' in data and isinstance(data['sms_notifications'], bool) and hasattr(user, 'sms_notifications'):
            user.sms_notifications = data['sms_notifications']
            
        if 'marketing_emails' in data and isinstance(data['marketing_emails'], bool) and hasattr(user, 'marketing_emails'):
            user.marketing_emails = data['marketing_emails']
            
        if 'notification_sound' in data and isinstance(data['notification_sound'], bool) and hasattr(user, 'notification_sound'):
            user.notification_sound = data['notification_sound']
            
        if 'vibrate' in data and isinstance(data['vibrate'], bool) and hasattr(user, 'vibrate'):
            user.vibrate = data['vibrate']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Notification preferences updated successfully',
            'data': {
                'email_notifications': getattr(user, 'email_notifications', True),
                'push_notifications': getattr(user, 'push_notifications', True),
                'sms_notifications': getattr(user, 'sms_notifications', False),
                'marketing_emails': getattr(user, 'marketing_emails', False),
                'notification_sound': getattr(user, 'notification_sound', True),
                'vibrate': getattr(user, 'vibrate', True)
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating notification preferences: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating notification preferences'
        }), 500

# ==============================================
# Chat Endpoints
# ==============================================

@api_bp.route('/chat/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """
    Get list of conversations for the current user
    Query Parameters:
    - limit: Number of conversations to return (default: 20, max: 100)
    - offset: For pagination (default: 0)
    """
    try:
        current_user_id = get_jwt_identity()
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = int(request.args.get('offset', 0))
        
        # Get all unique conversation partners with their latest message time
        sent_messages = db.session.query(
            Message.receiver_id.label('partner_id'),
            func.max(Message.created_at).label('latest_time')
        ).filter(
            Message.sender_id == current_user_id
        ).group_by(Message.receiver_id)
        
        received_messages = db.session.query(
            Message.sender_id.label('partner_id'),
            func.max(Message.created_at).label('latest_time')
        ).filter(
            Message.receiver_id == current_user_id
        ).group_by(Message.sender_id)
        
        # Combine using UNION to get all unique conversations
        all_conversations = sent_messages.union(received_messages).subquery()
        
        # Get the latest message time for each conversation
        latest_conversations = db.session.query(
            all_conversations.c.partner_id,
            func.max(all_conversations.c.latest_time).label('latest_time')
        ).group_by(all_conversations.c.partner_id).subquery()
        
        # Get the actual message details
        conversations = db.session.query(
            Message,
            User.full_name,
            User.photo,
            User.work,
            db.func.count(Message.id).filter(Message.receiver_id == current_user_id, Message.is_read == False).label('unread_count')
        ).join(
            latest_conversations,
            db.and_(
                db.or_(
                    db.and_(
                        Message.sender_id == current_user_id,
                        Message.receiver_id == latest_conversations.c.partner_id
                    ),
                    db.and_(
                        Message.receiver_id == current_user_id,
                        Message.sender_id == latest_conversations.c.partner_id
                    )
                ),
                Message.created_at == latest_conversations.c.latest_time
            )
        ).join(
            User,
            User.id == latest_conversations.c.partner_id
        ).group_by(
            latest_conversations.c.partner_id,
            Message.id,
            User.id
        ).order_by(
            latest_conversations.c.latest_time.desc()
        ).offset(offset).limit(limit).all()
        
        # Get unread counts for all conversations
        unread_counts = db.session.query(
            Message.sender_id,
            func.count(Message.id).label('count')
        ).filter(
            Message.receiver_id == current_user_id,
            Message.is_read == False
        ).group_by(Message.sender_id).all()
        
        unread_dict = {user_id: count for user_id, count in unread_counts}
        
        result = []
        for msg, full_name, photo, work, _ in conversations:
            partner_id = msg.receiver_id if msg.sender_id == current_user_id else msg.sender_id
            result.append({
                'user_id': partner_id,
                'full_name': full_name,
                'photo': url_for('serve_profile_pic', filename=photo, _external=True) if photo else url_for('static', filename='img/default-avatar.png', _external=True),
                'profession': work,
                'last_message': {
                    'id': msg.id,
                    'content': msg.content,
                    'is_read': msg.is_read,
                    'created_at': msg.created_at.isoformat(),
                    'is_sent': msg.sender_id == current_user_id
                },
                'unread_count': unread_dict.get(partner_id, 0)
            })
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting conversations: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch conversations'
        }), 500

@api_bp.route('/chat/messages', methods=['GET'])
@api_bp.route('/chat/messages/<int:other_user_id>', methods=['GET'])
@jwt_required()
def get_messages(other_user_id=None):
    """
    Get messages between current user and another user
    Query Parameters:
    - other_user_id: ID of the other user (required)
    - limit: Number of messages to return (default: 50, max: 100)
    - page: Page number for pagination (default: 1)
    - before: Message ID to get messages before (alternative to page)
    """
    try:
        current_user_id = get_jwt_identity()
        # Get other_user_id from URL path or query parameter
        other_user_id = other_user_id or request.args.get('other_user_id')
        
        if not other_user_id:
            return jsonify({
                'status': 'error',
                'message': 'other_user_id is required'
            }), 400
            
        try:
            other_user_id = int(other_user_id)
        except (ValueError, TypeError):
            return jsonify({
                'status': 'error',
                'message': 'Invalid other_user_id'
            }), 400
            
        limit = min(int(request.args.get('limit', 50)), 100)
        page = max(int(request.args.get('page', 1)), 1)
        before = request.args.get('before')
        
        query = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user_id, Message.receiver_id == other_user_id),
                and_(Message.sender_id == other_user_id, Message.receiver_id == current_user_id)
            )
        )
        
        # Apply pagination
        if before:
            query = query.filter(Message.id < before)
            messages = query.order_by(Message.id.desc()).limit(limit).all()
        else:
            # Calculate offset for page-based pagination
            offset = (page - 1) * limit
            messages = query.order_by(Message.id.desc()).offset(offset).limit(limit).all()
        
        # Mark messages as read
        unread_messages = [msg for msg in messages if msg.receiver_id == current_user_id and not msg.is_read]
        if unread_messages:
            now = datetime.utcnow()
            for msg in unread_messages:
                msg.is_read = True
                msg.read_at = now
            db.session.commit()
        
        # Get total count for pagination
        total_messages = query.count()
        total_pages = (total_messages + limit - 1) // limit  # Ceiling division
        
        result = [{
            'id': msg.id,
            'content': msg.content,
            'is_read': msg.is_read,
            'created_at': msg.created_at.isoformat(),
            'is_sent': msg.sender_id == current_user_id,
            'attachment': url_for('static', filename=msg.attachment, _external=True) if msg.attachment else None
        } for msg in messages]
        
        # Sort by created_at in ascending order (oldest first)
        result.sort(key=lambda x: x['created_at'])
        
        return jsonify({
            'status': 'success',
            'data': result,
            'pagination': {
                'total': total_messages,
                'page': page,
                'per_page': limit,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting messages: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch messages'
        }), 500

@api_bp.route('/chat/send', methods=['POST'])
@api_bp.route('/chat/messages', methods=['POST'])
@jwt_required()
def send_message():
    """
    Send a message to another user
    Expected JSON payload:
    {
        "receiver_id": 123,
        "content": "Hello!",
        "attachment": "path/to/file.jpg"  # Optional
    }
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'receiver_id' not in data or 'content' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Receiver ID and content are required'
            }), 400
            
        receiver_id = data['receiver_id']
        content = data['content'].strip()
        
        if not content and 'attachment' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Message content or attachment is required'
            }), 400
            
        # Check if receiver exists
        receiver = User.query.get(receiver_id)
        if not receiver:
            return jsonify({
                'status': 'error',
                'message': 'Recipient not found'
            }), 404
            
        # Create message
        message = Message(
            sender_id=current_user_id,
            receiver_id=receiver_id,
            content=content,
            attachment=data.get('attachment'),
            is_read=False
        )
        
        db.session.add(message)
        db.session.commit()
        
        # TODO: Send push notification to receiver
        
        return jsonify({
            'status': 'success',
            'message': 'Message sent successfully',
            'data': {
                'id': message.id,
                'content': message.content,
                'is_read': message.is_read,
                'created_at': message.created_at.isoformat(),
                'is_sent': True,
                'attachment': url_for('static', filename=message.attachment, _external=True) if message.attachment else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error sending message: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to send message'
        }), 500

@api_bp.route('/chat/messages/delete', methods=['POST', 'DELETE'])
@api_bp.route('/chat/messages/<int:message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(message_id=None):
    """
    Delete a message (soft delete)
    
    Supports both:
    - DELETE /api/v1/chat/messages/123
    - POST /api/v1/chat/delete with JSON body: {"message_id": 123}
    """
    try:
        current_user_id = get_jwt_identity()
        
        # If message_id is not in URL, get it from request body
        if message_id is None:
            data = request.get_json() or {}
            if 'message_id' not in data:
                return jsonify({
                    'status': 'error',
                    'message': 'Message ID is required'
                }), 400
            message_id = data['message_id']
        
        # Get the message
        message = Message.query.filter_by(id=message_id).first()
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'Message not found or already deleted'
            }), 404
            
        # Check if the current user is the sender or receiver
        if message.sender_id != current_user_id and message.receiver_id != current_user_id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized to delete this message'
            }), 403
            
        # Soft delete the message (mark as deleted)
        message.is_deleted = True
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Message deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting message: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to delete message'
        }), 500

@api_bp.route('/chat/clear', methods=['POST'])
@jwt_required()
def clear_chat():
    """
    Clear chat history with a specific user
    Expected JSON payload:
    {
        "other_user_id": 123  # ID of the other user in the conversation
    }
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'other_user_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'other_user_id is required'
            }), 400
            
        other_user_id = data['other_user_id']
        
        # Delete all messages between the two users
        deleted = db.session.execute(
            delete(Message)
            .where(
                or_(
                    and_(
                        Message.sender_id == current_user_id,
                        Message.receiver_id == other_user_id
                    ),
                    and_(
                        Message.sender_id == other_user_id,
                        Message.receiver_id == current_user_id
                    )
                )
            )
        )
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Chat history cleared successfully. {deleted.rowcount} messages removed.'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error clearing chat history: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to clear chat history'
        }), 500

@api_bp.route('/chat/messages/read', methods=['POST'])
@jwt_required()
def mark_messages_read():
    """
    Mark messages as read
    Expected JSON payload:
    {
        "message_ids": [1, 2, 3],  # Optional: specific message IDs to mark as read
        "sender_id": 123            # Optional: mark all messages from this sender as read
    }
    
    At least one of message_ids or sender_id must be provided
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or ('message_ids' not in data and 'sender_id' not in data):
            return jsonify({
                'status': 'error',
                'message': 'Either message_ids or sender_id must be provided'
            }), 400
            
        updated_count = 0
        
        # Mark specific messages as read if message_ids are provided
        if 'message_ids' in data and isinstance(data['message_ids'], list):
            message_ids = [int(msg_id) for msg_id in data['message_ids'] if str(msg_id).isdigit()]
            if message_ids:
                # Update only messages sent to current user
                result = Message.query.filter(
                    Message.id.in_(message_ids),
                    Message.receiver_id == current_user_id,
                    Message.is_read == False
                ).update({
                    Message.is_read: True,
                    Message.read_at: datetime.utcnow()
                }, synchronize_session=False)
                updated_count += result
        
        # Mark all unread messages from a specific sender as read
        if 'sender_id' in data and str(data['sender_id']).isdigit():
            sender_id = int(data['sender_id'])
            # Verify sender exists
            if User.query.get(sender_id):
                result = Message.query.filter(
                    Message.sender_id == sender_id,
                    Message.receiver_id == current_user_id,
                    Message.is_read == False
                ).update({
                    Message.is_read: True,
                    Message.read_at: datetime.utcnow()
                }, synchronize_session=False)
                updated_count += result
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Marked {updated_count} messages as read'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error marking messages as read: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to mark messages as read'
        }), 500

@api_bp.route('/auth/forgot-password', methods=['POST'])
@limiter.limit("5 per hour")  # Rate limiting to prevent abuse
def forgot_password():
    """
    Handle forgot password request
    Expected JSON payload:
    {
        "email": "user@example.com"
    }
    """
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Email is required'
            }), 400
            
        email = data['email'].strip().lower()
        user = User.query.filter_by(email=email).first()
        
        # Always return success to prevent email enumeration
        if not user:
            current_app.logger.warning(f'Password reset requested for non-existent email: {email}')
            return jsonify({
                'status': 'success',
                'message': 'If an account with this email exists, a password reset link has been sent.'
            }), 200
            
        # Generate reset token (expires in 1 hour)
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = serializer.dumps(user.email, salt='password-reset-salt')
        
        # Create reset link
        frontend_url = current_app.config.get('FRONTEND_URL', request.host_url.rstrip('/'))
        reset_url = f"{frontend_url}/reset-password?token={token}"
        
        # Send email with reset link
        subject = "Password Reset Request"
        html = f"""
        <p>Hello {user.full_name or 'User'},</p>
        <p>You requested to reset your password. Click the link below to set a new password:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request this, please ignore this email.</p>
        """
        
        msg = MailMessage(
            subject=subject,
            recipients=[user.email],
            html=html,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        
        try:
            mail.send(msg)
            current_app.logger.info(f'Password reset email sent to {user.email}')
        except Exception as e:
            current_app.logger.error(f'Error sending password reset email: {str(e)}')
            return jsonify({
                'status': 'error',
                'message': 'Failed to send password reset email. Please try again later.'
            }), 500
            
        return jsonify({
            'status': 'success',
            'message': 'If an account with this email exists, a password reset link has been sent.'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error in forgot_password: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while processing your request.'
        }), 500

@api_bp.route('/auth/reset-password', methods=['POST'])
@limiter.limit("5 per hour")  # Rate limiting to prevent abuse
def reset_password():
    """
    Handle password reset
    Expected JSON payload:
    {
        "token": "reset_token_from_email",
        "new_password": "NewSecurePass123!"
    }
    """
    try:
        data = request.get_json()
        if not data or 'token' not in data or 'new_password' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Token and new password are required'
            }), 400
            
        token = data['token']
        new_password = data['new_password']
        
        # Validate password strength
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
        
        # Verify token
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(
                token,
                salt='password-reset-salt',
                max_age=3600  # 1 hour expiration
            )
        except SignatureExpired:
            return jsonify({
                'status': 'error',
                'message': 'The password reset link has expired. Please request a new one.'
            }), 400
        except BadSignature:
            return jsonify({
                'status': 'error',
                'message': 'Invalid or expired token. Please request a new password reset.'
            }), 400
            
        # Find user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found.'
            }), 404
            
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        current_app.logger.info(f'Password reset successful for user: {user.email}')
        
        return jsonify({
            'status': 'success',
            'message': 'Your password has been reset successfully.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in reset_password: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while resetting your password.'
        }), 500

@api_bp.route('/profile_pic/<filename>')
def serve_profile_pic_route(filename):
    return serve_profile_pic(filename)

@api_bp.route('/verify/status', methods=['GET'])
@jwt_required()
def get_verification_status():
    """
    Get the verification status of the current user
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'error': 'USER_NOT_FOUND'
            }), 404
            
        return jsonify({
            'success': True,
            'verified': user.verified,
            'verified_at': user.verified_at.isoformat() if user.verified_at else None,
            'verification_requested': user.verification_requested,
            'verification_requested_at': user.verification_requested_at.isoformat() if user.verification_requested_at else None
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting verification status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get verification status',
            'error': str(e)
        }), 500

@api_bp.route('/verify/request', methods=['POST'])
@jwt_required()
def request_verification():
    """
    Request verification for the current user
    Expected JSON payload:
    {
        "document_type": "aadhaar",  // or 'pan', 'passport', 'driving_license'
        "document_number": "XXXX-XXXX-XXXX",
        "document_photo": "base64_encoded_image"  // Optional
    }
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'error': 'USER_NOT_FOUND'
            }), 404
            
        data = request.get_json()
        
        # Validate required fields
        if not data or 'document_type' not in data or 'document_number' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required fields: document_type and document_number are required',
                'error': 'MISSING_FIELDS'
            }), 400
            
        # Save verification request
        user.verification_requested = True
        user.verification_requested_at = datetime.utcnow()
        user.verification_document_type = data['document_type']
        user.verification_document_number = data['document_number']
        
        # Save document photo if provided
        if 'document_photo' in data and data['document_photo']:
            photo_path = save_base64_image(data['document_photo'], user_id)
            if photo_path:
                user.verification_document_photo = photo_path
        
        db.session.commit()
        
        # TODO: Notify admin about the verification request
        
        return jsonify({
            'success': True,
            'message': 'Verification request submitted successfully',
            'verification_requested': True,
            'verification_requested_at': user.verification_requested_at.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error requesting verification: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to submit verification request',
            'error': str(e)
        }), 500

@api_bp.route('/verify/update', methods=['POST'])
@jwt_required()
def update_verification_status():
    """
    Update verification status (Admin only)
    Expected JSON payload:
    {
        "user_id": 123,
        "status": true,  // or false to revoke verification
        "reason": "Document verified successfully"  // Optional reason for approval/rejection
    }
    """
    try:
        # Check if current user is admin
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Unauthorized: Admin access required',
                'error': 'UNAUTHORIZED'
            }), 403
            
        data = request.get_json()
        
        # Validate required fields
        if not data or 'user_id' not in data or 'status' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required fields: user_id and status are required',
                'error': 'MISSING_FIELDS'
            }), 400
            
        # Get target user
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found',
                'error': 'USER_NOT_FOUND'
            }), 404
            
        # Update verification status
        user.verified = data['status']
        if data['status']:
            user.verified_at = datetime.utcnow()
            user.verified_by = current_user_id
        else:
            user.verified_at = None
            user.verified_by = None
            
        # Save reason if provided
        if 'reason' in data:
            user.verification_notes = data['reason']
            
        db.session.commit()
        
        # TODO: Notify user about verification status update
        
        return jsonify({
            'success': True,
            'message': f"Verification {'approved' if data['status'] else 'revoked'} successfully",
            'verified': user.verified,
            'verified_at': user.verified_at.isoformat() if user.verified_at else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating verification status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update verification status',
            'error': str(e)
        }), 500

def serve_profile_pic(filename):
    try:
        current_app.logger.info(f"\n=== SERVING PROFILE PICTURE ===")
        current_app.logger.info(f"Requested filename: {filename}")
        
        if not filename or filename == 'None':
            current_app.logger.info("No filename provided, serving default avatar")
            return send_from_directory('static', 'img/default-avatar.png')
        
        # Security check to prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            current_app.logger.warning(f"Potential directory traversal attempt with filename: {filename}")
            return send_from_directory('static', 'img/default-avatar.png')
        
        # Get the upload folder from config or use default
        upload_folder = os.path.abspath(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'))
        current_app.logger.info(f"Using upload folder: {upload_folder}")
        
        # Check profile_pics directory first
        profile_pics_path = os.path.join(upload_folder, 'profile_pics')
        os.makedirs(profile_pics_path, exist_ok=True)
        
        # Check in profile_pics directory
        file_path = os.path.join(profile_pics_path, filename)
        current_app.logger.info(f"Checking for file at: {file_path}")
        
        if os.path.isfile(file_path):
            current_app.logger.info(f"Serving file from profile_pics: {file_path}")
            try:
                return send_from_directory(profile_pics_path, filename)
            except Exception as e:
                current_app.logger.error(f"Error serving from profile_pics: {str(e)}")
        
        # If not found, check root uploads directory
        root_file_path = os.path.join(upload_folder, filename)
        current_app.logger.info(f"File not found in profile_pics, checking: {root_file_path}")
        
        if os.path.isfile(root_file_path):
            current_app.logger.info(f"Serving file from uploads root: {root_file_path}")
            try:
                return send_from_directory(upload_folder, filename)
            except Exception as e:
                current_app.logger.error(f"Error serving from uploads root: {str(e)}")
        
        # Log directory structure for debugging
        try:
            current_app.logger.info("\n=== DIRECTORY STRUCTURE ===")
            
            # Log current working directory
            current_app.logger.info(f"Current working directory: {os.getcwd()}")
            
            # Log upload folder structure
            current_app.logger.info(f"\nUpload folder: {upload_folder}")
            if os.path.exists(upload_folder):
                for root, dirs, files in os.walk(upload_folder):
                    level = root.replace(upload_folder, '').count(os.sep)
                    indent = ' ' * 4 * level
                    current_app.logger.info(f"{indent}{os.path.basename(root)}/")
                    subindent = ' ' * 4 * (level + 1)
                    for f in files[:10]:  # Show first 10 files to avoid log spam
                        current_app.logger.info(f"{subindent}{f}")
                    if len(files) > 10:
                        current_app.logger.info(f"{subindent}... and {len(files)-10} more files")
            else:
                current_app.logger.error(f"Upload folder does not exist: {upload_folder}")
                
        except Exception as e:
            current_app.logger.error(f"Error listing directory contents: {str(e)}")
        
        current_app.logger.warning(f"File not found: {filename}, serving default avatar")
        return send_from_directory('static', 'img/default-avatar.png')
        
    except Exception as e:
        current_app.logger.error(f"Error serving profile picture {filename}: {str(e)}", exc_info=True)
        return send_from_directory('static', 'img/default-avatar.png')

@api_bp.route('/call', methods=['POST'])
@jwt_required()
def handle_call():
    """
    Handle call status updates from Flutter frontend
    
    Expected JSON payload:
    {
        "call_id": "unique_call_id",  # Optional for new calls
        "caller_id": 123,            # Required for new calls
        "callee_id": 456,            # Required for new calls
        "status": "initiated",       # initiated, accepted, rejected, completed, missed, failed
        "duration": 120,             # Optional, in seconds
        "cost": 10.5                 # Optional, in INR
    }
    
    Returns:
    {
        "status": "success/error",
        "message": "Status message",
        "call": { call_details }     # Current call state
    }
    """
    current_user_id = int(get_jwt_identity())
    
    # Log incoming request for debugging
    current_app.logger.info(f"[CALL] Incoming request from user {current_user_id}")
    current_app.logger.info(f"[CALL] Request headers: {dict(request.headers)}")
    
    # Get and validate JSON data
    if not request.is_json:
        current_app.logger.error("[CALL] Request must be JSON")
        return jsonify({
            'status': 'error',
            'message': 'Request must be JSON',
            'error': 'Invalid content type'
        }), 400
    
    try:
        data = request.get_json()
        current_app.logger.info(f"[CALL] Request data: {data}")
    except Exception as e:
        current_app.logger.error(f"[CALL] Failed to parse JSON: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Invalid JSON data',
            'error': str(e)
        }), 400
    
    # Validate required fields
    if not data:
        current_app.logger.error("[CALL] No data provided")
        return jsonify({
            'status': 'error',
            'message': 'No data provided',
            'error': 'Empty request body'
        }), 400
        
    if 'status' not in data:
        current_app.logger.error("[CALL] Status is required")
        return jsonify({
            'status': 'error',
            'message': 'Status is required',
            'error': 'Missing status field',
            'required_fields': ['status'],
            'valid_statuses': ['initiated', 'accepted', 'rejected', 'completed', 'missed', 'failed']
        }), 400
    
    try:
        call = None
        call_id = data.get('call_id')
        
        # Validate status value
        valid_statuses = ['initiated', 'accepted', 'rejected', 'completed', 'missed', 'failed']
        if data['status'] not in valid_statuses:
            current_app.logger.error(f"[CALL] Invalid status value: {data['status']}")
            return jsonify({
                'status': 'error',
                'message': f'Invalid status value. Must be one of: {valid_statuses}',
                'valid_statuses': valid_statuses
            }), 400
        
        if call_id:
            # Update existing call
            current_app.logger.info(f"[CALL] Updating existing call: {call_id}")
            call = Call.query.filter_by(call_id=call_id).first()
            if not call:
                current_app.logger.error(f"[CALL] Call not found: {call_id}")
                return jsonify({
                    'status': 'error',
                    'message': 'Call not found',
                    'error': 'call_not_found'
                }), 404
                
            # Verify user is part of the call
            if current_user_id not in [call.caller_id, call.callee_id]:
                current_app.logger.error(f"[CALL] User {current_user_id} not authorized to update call {call_id}")
                return jsonify({
                    'status': 'error',
                    'message': 'Unauthorized to update this call',
                    'error': 'unauthorized'
                }), 403
                
        else:
            # Create new call
            current_app.logger.info("[CALL] Creating new call")
            
            # Validate required fields for new call
            required_fields = ['caller_id', 'callee_id']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                current_app.logger.error(f"[CALL] Missing required fields: {missing_fields}")
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required fields: {missing_fields}',
                    'error': 'missing_fields',
                    'required_fields': required_fields
                }), 400
            
            # Verify caller and callee exist
            caller = User.query.get(data['caller_id'])
            callee = User.query.get(data['callee_id'])
            
            if not caller or not callee:
                current_app.logger.error(f"[CALL] Invalid user(s) - caller: {data['caller_id']}, callee: {data['callee_id']}")
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid caller or callee ID',
                    'error': 'invalid_user',
                    'caller_exists': bool(caller),
                    'callee_exists': bool(callee)
                }), 400
                
            # Ensure we're comparing integers with integers
            caller_id = int(data['caller_id'])
            callee_id = int(data['callee_id'])
            
            # Verify caller or callee is the current user
            if current_user_id not in [caller_id, callee_id]:
                current_app.logger.error(f"[CALL] User {current_user_id} not part of call between {caller_id} and {callee_id}")
                return jsonify({
                    'status': 'error',
                    'message': 'You must be part of the call',
                    'error': 'not_call_participant',
                    'current_user_id': current_user_id,
                    'caller_id': caller_id,
                    'callee_id': callee_id
                }), 403
                
            call_id = f"call_{uuid.uuid4().hex}"
            call = Call(
                call_id=call_id,
                caller_id=caller_id,  # Using the converted integer
                callee_id=callee_id,  # Using the converted integer
                status='initiated',
                duration=0,
                cost=0.0
            )
            db.session.add(call)
            current_app.logger.info(f"[CALL] New call created: {call_id} between {call.caller_id} and {call.callee_id}")
        
        # Update call status and other fields
        previous_status = call.status
        call.status = data['status']
        
        # Log status change
        current_app.logger.info(f"[CALL] Updating call {call_id} status from {previous_status} to {call.status}")
        
        # Update duration if provided and valid
        if 'duration' in data and isinstance(data['duration'], (int, float)) and data['duration'] >= 0:
            call.duration = data['duration']
            
        # Update cost if provided and valid
        if 'cost' in data and isinstance(data['cost'], (int, float)) and data['cost'] >= 0:
            call.cost = data['cost']
            
        # Update timestamps
        call.updated_at = datetime.utcnow()
        
        # If call is completed, calculate duration if not provided
        if call.status == 'completed' and not call.duration and call.created_at:
            call.duration = int((datetime.utcnow() - call.created_at).total_seconds())
            current_app.logger.info(f"[CALL] Calculated call duration: {call.duration} seconds")
        
        # Handle wallet deduction for completed calls
        if call.status == 'completed' and call.duration > 0:
            # Calculate call cost based on duration and rate
            call_rate = data.get('call_rate', 2.5)  # Default rate per minute
            duration_minutes = call.duration / 60.0
            calculated_cost = round(duration_minutes * call_rate, 2)
            
            # Use provided cost or calculated cost
            final_cost = data.get('cost', calculated_cost)
            call.cost = final_cost
            
            current_app.logger.info(f"[CALL] Call completed - Duration: {call.duration}s ({duration_minutes:.2f} min), Rate: ₹{call_rate}/min, Cost: ₹{final_cost}")
            
            # Deduct from caller's wallet
            try:
                caller = User.query.get(call.caller_id)
                if caller:
                    caller_balance = float(caller.wallet_balance) if caller.wallet_balance is not None else 0.0
                    
                    if caller_balance >= final_cost:
                        # Deduct from caller
                        caller.wallet_balance = round(caller_balance - final_cost, 2)
                        
                        # Create deduction transaction
                        deduction_transaction = Transaction(
                            user_id=call.caller_id,
                            amount=-final_cost,
                            transaction_type='debit',
                            status='completed',
                            description=f'Call charge: {duration_minutes:.1f} min @ ₹{call_rate}/min',
                            reference_id=call.call_id,
                            metadata={'type': 'call_charge', 'duration': call.duration, 'rate': call_rate}
                        )
                        db.session.add(deduction_transaction)
                        
                        # Add to callee's wallet (earnings)
                        callee = User.query.get(call.callee_id)
                        if callee:
                            callee_balance = float(callee.wallet_balance) if callee.wallet_balance is not None else 0.0
                            earning_amount = round(final_cost * 0.8, 2)  # 80% to callee, 20% platform fee
                            callee.wallet_balance = round(callee_balance + earning_amount, 2)
                            
                            # Create earning transaction
                            earning_transaction = Transaction(
                                user_id=call.callee_id,
                                amount=earning_amount,
                                transaction_type='credit',
                                status='completed',
                                description=f'Call earning: {duration_minutes:.1f} min @ ₹{call_rate}/min',
                                reference_id=call.call_id,
                                metadata={'type': 'call_earning', 'duration': call.duration, 'rate': call_rate}
                            )
                            db.session.add(earning_transaction)
                            
                            current_app.logger.info(f"[CALL] Wallet updated - Caller {call.caller_id}: -₹{final_cost}, Callee {call.callee_id}: +₹{earning_amount}")
                        
                    else:
                        current_app.logger.warning(f"[CALL] Insufficient balance for caller {call.caller_id}: ₹{caller_balance} < ₹{final_cost}")
                        # You might want to handle insufficient balance differently
                        
            except Exception as wallet_error:
                current_app.logger.error(f"[CALL] Wallet deduction error: {str(wallet_error)}")
                # Continue with call completion even if wallet operation fails
        
        db.session.commit()
        current_app.logger.info(f"[CALL] Call {call_id} updated successfully")
        
        # TODO: Send push notification for new calls
        
        return jsonify({
            'status': 'success',
            'message': f'Call {call.status} successfully',
            'call': call.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        error_id = str(uuid.uuid4())
        error_msg = f"[CALL] Error {error_id}: {str(e)}\n{traceback.format_exc()}"
        current_app.logger.error(error_msg)
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error': 'server_error',
            'error_id': error_id,
            'error_details': str(e) if current_app.debug else None
        }), 500

@api_bp.route('/user/<int:user_id>', methods=['GET'])
def api_get_user_profile(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Prepare date of birth in multiple formats for compatibility
        dob_iso = user.date_of_birth.isoformat() if user.date_of_birth else None
        
        profile_data = {
            'id': user.id,
            'full_name': user.full_name,
            'email': user.email,
            'photo_url': url_for('serve_profile_pic', filename=user.photo, _external=True) if user.photo else url_for('static', filename='img/default-avatar.png', _external=True),
            'profession': user.profession,
            'education': user.education,
            'experience': user.experience,
            'skills': user.skills.split(',') if user.skills else [],
            'work_experience': user.work_experience.split(',') if user.work_experience else [],
            'payment_charge': user.payment_charge,
            'payment_type': user.payment_type,
            'location': user.current_location,
            'bio': user.bio,
            'work': user.work,
            'average_rating': user.average_rating,
            'total_reviews': user.total_reviews,
            'profile_views': user.profile_views,
            'is_online': user.is_online,
            'phone': user.phone,  # Add phone number to the response
            # Include date_of_birth in multiple formats for compatibility
            'date_of_birth': dob_iso,
            'dateOfBirth': dob_iso,  # Add camelCase version for Flutter
            'user': {  # Add a nested user object as per Flutter's expectation
                'date_of_birth': dob_iso,
                'dateOfBirth': dob_iso
            }
        }

        return jsonify({'success': True, 'user': profile_data}), 200
    except Exception as e:
        print(f"[API PROFILE ERROR] {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@api_bp.route('/profiles', methods=['GET'])
@jwt_required()
def get_profiles():
    """
    Get a list of user profiles with filtering and pagination
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    - user_type: Filter by user type (worker/client)
    - profession: Filter by profession
    - search: Search in name, profession, or bio
    - min_rating: Minimum average rating (0-5)
    - available: Filter by availability (true/false)
    - sort: Sort by (rating, newest, oldest)
    """
    try:
        
        # Pagination
        page = max(1, request.args.get('page', 1, type=int))
        per_page = min(100, max(1, request.args.get('per_page', 20, type=int)))
        
        # Base query
        query = User.query.filter(User.active == True)
        
        # Apply filters
        user_type = request.args.get('user_type')
        if user_type in ['worker', 'client']:
            query = query.filter(User.user_type == user_type)
        
        profession = request.args.get('profession')
        if profession:
            query = query.filter(
                or_(
                    User.profession.ilike(f'%{profession}%'),
                    User.work.ilike(f'%{profession}%')
                )
            )
        
        search = request.args.get('search')
        if search:
            search = f'%{search}%'
            query = query.filter(
                or_(
                    User.full_name.ilike(search),
                    User.profession.ilike(search),
                    User.work.ilike(search),
                    User.bio.ilike(search)
                )
            )
        
        min_rating = request.args.get('min_rating', type=float)
        if min_rating is not None:
            query = query.filter(User.average_rating >= min_rating)
        
        available = request.args.get('available')
        if available is not None:
            query = query.filter(User.availability == 'available')
        
        # Sorting
        sort = request.args.get('sort', 'newest')
        if sort == 'rating':
            query = query.order_by(User.average_rating.desc())
        elif sort == 'oldest':
            query = query.order_by(User.created_at.asc())
        else:  # newest
            query = query.order_by(User.created_at.desc())
        
        # Paginate results
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items
        
        # Prepare response
        user_list = []
        current_app.logger.info(f'Processing {len(users)} users for profiles endpoint')
        
        for user in users:
            current_app.logger.info(f'User {user.id} - Experience: {user.experience}, Type: {type(user.experience)}')
            # Build base user data
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'phone': user.phone,  # Add phone number to the response
                'user_type': user.user_type,
                'profession': user.profession or user.work or '',
                'bio': user.bio or '',
                'photo': url_for('static', filename=f'uploads/{user.photo}', _external=True) if user.photo else None,
                'average_rating': float(user.average_rating) if user.average_rating is not None else 0.0,
                'total_reviews': user.total_reviews or 0,
                'is_online': user.is_online,
                'last_active': user.last_active.isoformat() if user.last_active else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'live_location': user.live_location or '',
                'current_location': user.current_location or '',
                'location': (user.live_location or user.current_location or ''),  # For backward compatibility
                'distance': None,
                'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
                'dateOfBirth': user.date_of_birth.isoformat() if user.date_of_birth else None,  # camelCase for Flutter
                # Include all fields with default values to ensure consistent response structure
                'experience': str(user.experience) if user.experience is not None else '',
                'education': '',
                'skills': [],
                'categories': [],
                'availability': False,
                'payment_charge': None,
                'payment_type': '',
                'hourly_rate': None  # Alias for payment_charge for Flutter app
            }
            
            # Update with actual values if they exist
            if user.user_type == 'worker':
                user_data.update({
                    'experience': str(user.experience) if user.experience is not None else '',  # Ensure experience is a string
                    'education': user.education or '',
                    'skills': user.skills.split(',') if user.skills else [],
                    'categories': user.categories.split(',') if user.categories else [],
                    'availability': user.availability if user.availability is not None else False,
                    'payment_charge': float(user.payment_charge) if user.payment_charge else None,
                    'payment_type': user.payment_type or '',
                    'hourly_rate': float(user.payment_charge) if user.payment_charge else None  # Alias for Flutter
                })
            
            user_list.append(user_data)
        
        return jsonify({
            'status': 'success',
            'data': user_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching profiles: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching profiles',
            'error': str(e)
        }), 500

@api_bp.route('/save-user', methods=['POST'])
@jwt_required()
@cross_origin()
@limiter.limit("50 per hour")
def save_user():
    """
    Save/unsave a user profile for later viewing
    Expected JSON payload:
    {
        "user_id": 123,
        "action": "save" or "unsave"
    }
    """
    try:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
            
        try:
            # Convert to integer
            current_user_id = int(current_user_id)
        except (ValueError, TypeError) as e:
            return jsonify({
                'status': 'error',
                'message': 'Invalid user ID format',
                'error': str(e)
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        user_id_to_save = data.get('user_id')
        action = data.get('action', 'save')
        
        if not user_id_to_save:
            return jsonify({
                'status': 'error',
                'message': 'user_id is required'
            }), 400
        
        if action not in ['save', 'unsave']:
            return jsonify({
                'status': 'error',
                'message': 'action must be either "save" or "unsave"'
            }), 400
        
        try:
            # Convert to integer
            user_id_to_save = int(user_id_to_save)
            current_user_id = int(current_user_id)
            
            # Check if user exists
            user_to_save = User.query.get(user_id_to_save)
            if not user_to_save:
                return jsonify({
                    'status': 'error',
                    'message': 'User not found'
                }), 404
        except (ValueError, TypeError) as e:
            return jsonify({
                'status': 'error',
                'message': 'Invalid user ID format',
                'error': str(e)
            }), 400
        
        # Prevent users from saving themselves
        if current_user_id == user_id_to_save:
            return jsonify({
                'status': 'error',
                'message': 'Cannot save your own profile'
            }), 400
        
        # Check if already saved
        existing_save = SavedUser.query.filter_by(
            user_id=current_user_id,
            saved_user_id=user_id_to_save
        ).first()
        
        if action == 'save':
            if existing_save:
                return jsonify({
                    'status': 'success',
                    'message': 'User already saved',
                    'data': {
                        'is_saved': True,
                        'saved_at': existing_save.created_at.isoformat()
                    }
                }), 200
            
            # Create new save
            new_save = SavedUser(
                user_id=current_user_id,
                saved_user_id=user_id_to_save
            )
            db.session.add(new_save)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'User saved successfully',
                'data': {
                    'is_saved': True,
                    'saved_at': new_save.created_at.isoformat()
                }
            }), 201
        
        else:  # unsave
            if not existing_save:
                return jsonify({
                    'status': 'success',
                    'message': 'User was not saved',
                    'data': {
                        'is_saved': False
                    }
                }), 200
            
            # Remove save
            db.session.delete(existing_save)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'User unsaved successfully',
                'data': {
                    'is_saved': False
                }
            }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in save_user: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while processing your request',
            'error': str(e)
        }), 500

@api_bp.route('/saved-users', methods=['GET'])
@jwt_required()
@cross_origin()
@limiter.limit("100 per hour")
def get_saved_users():
    """
    Get all saved users for the current user
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    """
    try:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
            
        try:
            # Convert to integer
            current_user_id = int(current_user_id)
        except (ValueError, TypeError) as e:
            return jsonify({
                'status': 'error',
                'message': 'Invalid user ID format',
                'error': str(e)
            }), 400
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Get saved users with pagination
        saved_users_query = db.session.query(SavedUser, User).join(
            User, SavedUser.saved_user_id == User.id
        ).filter(
            SavedUser.user_id == current_user_id,
            User.active == True
        ).order_by(SavedUser.created_at.desc())
        
        pagination = saved_users_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        saved_users_list = []
        for saved_user, user in pagination.items:
            user_data = {
                'id': user.id,
                'full_name': user.full_name,
                'profession': user.profession,
                'experience': user.experience,
                'education': user.education,
                'phone': user.phone,  # Using the correct phone field from User model
                'current_location': user.current_location,
                'skills': user.skills,
                'average_rating': user.average_rating,
                'total_reviews': user.total_reviews,
                'payment_type': user.payment_type,
                'payment_charge': user.payment_charge,
                'profile_photo': url_for('serve_profile_pic', filename=user.photo, _external=True) if user.photo else url_for('static', filename='img/default-avatar.png', _external=True),
                'saved_at': saved_user.created_at.isoformat(),
                'is_online': user.is_online,
                'last_active': user.last_active.isoformat() if user.last_active else None
            }
            saved_users_list.append(user_data)
        
        return jsonify({
            'status': 'success',
            'data': saved_users_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f'Error in get_saved_users: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while fetching saved users',
            'error': str(e)
        }), 500

@api_bp.route('/report-user', methods=['POST'])
@jwt_required()
@cross_origin()
@limiter.limit("10 per hour")
def report_user():
    """
    Report a user for inappropriate behavior
    Expected JSON payload:
    {
        "user_id": 123,
        "reason": "spam",
        "description": "Optional detailed description"
    }
    
    Valid reasons: spam, harassment, fake_profile, inappropriate_content, scam, other
    """
    try:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
            
        try:
            # Convert to integer
            current_user_id = int(current_user_id)
        except (ValueError, TypeError) as e:
            return jsonify({
                'status': 'error',
                'message': 'Invalid user ID format',
                'error': str(e)
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        user_id_to_report = data.get('user_id')
        reason = data.get('reason')
        description = data.get('description', '')
        
        # Validate required fields
        if not user_id_to_report:
            return jsonify({
                'status': 'error',
                'message': 'user_id is required'
            }), 400
        
        if not reason:
            return jsonify({
                'status': 'error',
                'message': 'reason is required'
            }), 400
        
        # Map frontend reasons to backend reason codes
        reason_mapping = {
            'Inappropriate Profile Content': 'inappropriate_content',
            'Spam or Scam Behavior': 'spam',
            'Harassment or Hate Speech': 'harassment',
            'Impersonation or Fake Profile': 'fake_profile',
            'Other': 'other'
        }
        
        # Get the backend reason code, defaulting to 'other' if not found
        backend_reason = reason_mapping.get(reason, 'other')
        
        # If it's an 'Other' reason, use the description if provided
        if backend_reason == 'other' and description:
            backend_reason = description[:100]  # Limit length to 100 chars
        
        # Check if user exists
        user_to_report = User.query.get(user_id_to_report)
        if not user_to_report:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
        
        # Prevent users from reporting themselves
        if str(current_user_id) == str(user_id_to_report):
            return jsonify({
                'status': 'error',
                'message': 'Cannot report your own profile'
            }), 400
        
        # Check if user already reported this user recently (within 24 hours)
        recent_report = Report.query.filter_by(
            reporter_id=current_user_id,
            reported_user_id=user_id_to_report
        ).filter(
            Report.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).first()
        
        if recent_report:
            return jsonify({
                'status': 'error',
                'message': 'You have already reported this user recently. Please wait 24 hours before reporting again.'
            }), 429
        
        # Create new report
        new_report = Report(
            reporter_id=current_user_id,
            reported_user_id=user_id_to_report,
            reason=reason,
            description=description[:1000] if description else None  # Limit description length
        )
        
        db.session.add(new_report)
        db.session.commit()
        
        # Log the report for admin review
        current_app.logger.info(f'User {current_user_id} reported user {user_id_to_report} for {reason}')
        
        return jsonify({
            'status': 'success',
            'message': 'Report submitted successfully. Our team will review it shortly.',
            'data': {
                'report_id': new_report.id,
                'submitted_at': new_report.created_at.isoformat()
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in report_user: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while submitting your report',
            'error': str(e)
        }), 500

@api_bp.route('/check-saved-status/<path:user_id>', methods=['GET'])
@jwt_required()
@cross_origin()
@limiter.limit("200 per hour")
def check_saved_status(user_id):
    """
    Check if a user is saved by the current user
    """
    try:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
            
        try:
            # Convert to integer
            current_user_id = int(current_user_id)
        except (ValueError, TypeError) as e:
            return jsonify({
                'status': 'error',
                'message': 'Invalid user ID format',
                'error': str(e)
            }), 400
            
        try:
            # Convert IDs to integers
            current_user_id = int(current_user_id)
            user_id = int(user_id)
        except (ValueError, TypeError) as e:
            return jsonify({
                'status': 'error',
                'message': 'Invalid user ID format',
                'error': str(e)
            }), 400
        
        # Check if saved
        saved = SavedUser.query.filter_by(
            user_id=current_user_id,
            saved_user_id=user_id
        ).first()
        
        return jsonify({
            'status': 'success',
            'data': {
                'is_saved': saved is not None,
                'saved_at': saved.created_at.isoformat() if saved else None
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f'Error in check_saved_status: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while checking saved status',
            'error': str(e)
        }), 500
