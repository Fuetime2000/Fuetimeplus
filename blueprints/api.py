from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    get_jwt_identity,
    jwt_required
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import re
import requests
import math
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from models.user import User
from extensions import db

api_bp = Blueprint('api', __name__)

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

@api_bp.route('/v1/auth/register', methods=['POST'])
def register():
    """
    Register a new user
    Expected JSON payload:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "full_name": "John Doe",
        "phone": "+1234567890",
        "user_type": "worker"  # or "client"
    }
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'full_name', 'phone', 'user_type']
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
    
    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({
            'status': 'error',
            'message': 'Email already registered'
        }), 409
    
    # Check if phone already exists
    if User.query.filter_by(phone=data['phone']).first():
        return jsonify({
            'status': 'error',
            'message': 'Phone number already registered'
        }), 409
    
    try:
        # Create new user
        user = User(
            email=data['email'],
            full_name=data['full_name'],
            phone=data['phone'],
            user_type=data['user_type'],
            active=True
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'data': {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'user_type': user.user_type,
                    'phone': user.phone,
                    'is_verified': user.email_verified
                },
                'tokens': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'token_type': 'bearer'
                }
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Registration error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during registration',
            'error': str(e)
        }), 500

@api_bp.route('/v1/auth/login', methods=['POST'])
def login():
    """
    User login
    Expected JSON payload:
    {
        "email": "user@example.com",
        "password": "SecurePass123!"
    }
    """
    data = request.get_json()
    
    # Validate required fields
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Email and password are required'
        }), 400
    
    try:
        # Find user by email
        user = User.query.filter_by(email=data['email']).first()
        
        # Check if user exists and password is correct
        if not user or not user.check_password(data['password']):
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
        
        # Update last login time
        user.last_active = db.func.now()
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'user_type': user.user_type,
                    'phone': user.phone,
                    'is_verified': user.email_verified,
                    'wallet_balance': user.wallet_balance,
                    'profile_picture': user.photo
                },
                'tokens': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'token_type': 'bearer'
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Login error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during login',
            'error': str(e)
        }), 500

@api_bp.route('/v1/calculate-distance', methods=['GET'])
def calculate_distance_endpoint():
    """
    Calculate distance between two locations
    Query parameters:
    - from: Location string or lat,lng of starting point
    - to: Location string or lat,lng of destination
    """
    from_location = request.args.get('from')
    to_location = request.args.get('to')
    
    current_app.logger.info(f"Distance calculation request - from: '{from_location}', to: '{to_location}'")
    
    if not from_location or not to_location:
        error_msg = f"Missing required parameters. from: '{from_location}', to: '{to_location}'"
        current_app.logger.warning(error_msg)
        return jsonify({
            'error': 'Both from and to locations are required',
            'details': error_msg,
            'success': False
        }), 400
    
    # Always calculate distance using coordinates, even if location strings are identical
    # because the same location name might refer to different coordinates
    current_app.logger.info("Proceeding with distance calculation")
    
    try:
        # Get coordinates for both locations with detailed error reporting
        current_app.logger.info(f"Getting coordinates for locations...")
        try:
            from_coords = get_coordinates(from_location)
            to_coords = get_coordinates(to_location)
            
            current_app.logger.info(f"Got coordinates - from: {from_coords}, to: {to_coords}")
            
            error_details = []
            if not from_coords:
                error_msg = f"Could not determine coordinates for: '{from_location}'"
                error_details.append(error_msg)
                current_app.logger.warning(error_msg)
                
            if not to_coords:
                error_msg = f"Could not determine coordinates for: '{to_location}'"
                error_details.append(error_msg)
                current_app.logger.warning(error_msg)
                
            if error_details:
                response = {
                    'error': 'Location resolution failed',
                    'details': '; '.join(error_details),
                    'from_location': from_location,
                    'to_location': to_location,
                    'success': False
                }
                current_app.logger.error(f"Location resolution failed: {response}")
                return jsonify(response), 400
                
        except Exception as e:
            error_msg = f"Error getting coordinates: {str(e)}"
            current_app.logger.error(error_msg, exc_info=True)
            return jsonify({
                'error': 'Error processing locations',
                'details': error_msg,
                'success': False
            }), 400
        
        try:
            # Calculate distance in kilometers
            distance_km = calculate_distance(from_coords, to_coords)
            
            # Ensure we don't show 0m away
            if distance_km < 0.1:  # Less than 100m
                # Show at least 100m for very close distances
                distance_m = max(100, int(distance_km * 1000))
                distance_display = f"{distance_m}m away"
            elif distance_km < 1:  # Less than 1km
                # Show in 100m increments, minimum 0.1km (100m)
                distance_km = max(0.1, distance_km)
                distance_display = f"{distance_km:.1f}km away"
            else:  # 1km or more
                distance_display = f"{distance_km:.1f}km away"
            
            return jsonify({
                'distance_km': distance_km,
                'distance_display': distance_display,
                'success': True
            })
            
        except ValueError as ve:
            current_app.logger.error(f"Invalid coordinate values: {ve}")
            return jsonify({
                'error': 'Invalid location coordinates',
                'details': str(ve),
                'success': False
            }), 400
            
    except Exception as e:
        error_msg = f"Error calculating distance: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        return jsonify({
            'error': 'Failed to calculate distance',
            'details': str(e),
            'success': False
        }), 500

@api_bp.route('/v1/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user's profile
    Requires valid access token in Authorization header
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
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
                'full_name': user.full_name,
                'user_type': user.user_type,
                'phone': user.phone,
                'is_verified': user.email_verified,
                'wallet_balance': user.wallet_balance,
                'profile_picture': user.photo,
                'is_online': user.is_online,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'Get user error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve user data',
            'error': str(e)
        }), 500
