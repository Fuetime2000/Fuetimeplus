from flask import Blueprint, request, jsonify, current_app, url_for
from flask_jwt_extended import jwt_required
from extensions import limiter
from models.user import User
from sqlalchemy import or_
from datetime import datetime

search_bp = Blueprint('search_api', __name__)

@search_bp.route('/api/search', methods=['GET'])
@jwt_required(optional=True)
@limiter.limit("100 per day")
def search_users():
    """
    Search for users with filters
    
    Query Parameters:
    - query: Search term (searches in name, skills, work)
    - category: Filter by skill category
    - location: Filter by location
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 50)
    - include_inactive: Include inactive users (default: false)
    
    Returns:
    {
        'success': bool,
        'data': [
            {
                'id': int,
                'username': str,
                'full_name': str,
                'photo_url': str,
                'work': str,
                'current_location': str,
                'skills': list,
                'average_rating': float,
                'review_count': int,
                'is_online': bool,
                'last_active': str (ISO format) or null,
                'hourly_rate': float or null,
                'experience': str
            },
            ...
        ],
        'pagination': {
            'page': int,
            'per_page': int,
            'total_pages': int,
            'total_items': int,
            'has_next': bool,
            'has_prev': bool
        }
    }
    """
    try:
        # Get query parameters with defaults
        query = request.args.get('query', '').strip()
        category = request.args.get('category', '').strip()
        location = request.args.get('location', '').strip()
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(50, max(1, int(request.args.get('per_page', 20))))
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        
        # Start building the query
        search_query = User.query
        
        # Apply search filters
        if query:
            search = f'%{query}%'
            search_query = search_query.filter(
                or_(
                    User.full_name.ilike(search),
                    User.skills.ilike(search),
                    User.work.ilike(search),
                    User.profession.ilike(search)
                )
            )
        
        if category:
            search_query = search_query.filter(User.categories.ilike(f'%{category}%'))
        
        if location:
            search_query = search_query.filter(
                or_(
                    User.current_location.ilike(f'%{location}%'),
                    User.live_location.ilike(f'%{location}%')
                )
            )
        
        # Filter out inactive users unless explicitly requested
        if not include_inactive:
            search_query = search_query.filter(User.active == True)
        
        # Order by most recently active
        search_query = search_query.order_by(User.last_active.desc())
        
        # Paginate results
        pagination = search_query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items
        
        # Format response
        user_list = []
        for user in users:
            # Build photo URL
            photo_url = None
            if user.photo:
                photo_url = url_for('static', filename=f'uploads/{user.photo}', _external=True)
            
            # Get skills as list
            skills = []
            if user.skills:
                skills = [s.strip() for s in user.skills.split(',') if s.strip()]
            
            # Get categories as list
            categories = []
            if user.categories:
                categories = [c.strip() for c in user.categories.split(',') if c.strip()]
            
            # Format last active time
            last_active = None
            if hasattr(user, 'last_active') and user.last_active:
                if isinstance(user.last_active, datetime):
                    last_active = user.last_active.isoformat()
                else:
                    last_active = user.last_active
            
            user_data = {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'photo_url': photo_url,
                'work': user.work or user.profession or '',
                'current_location': user.current_location or user.live_location or '',
                'skills': skills,
                'categories': categories,
                'average_rating': float(user.average_rating) if user.average_rating is not None else 0.0,
                'review_count': user.reviews_received.count() if hasattr(user, 'reviews_received') else 0,
                'is_online': user.is_online if hasattr(user, 'is_online') else False,
                'last_active': last_active,
                'hourly_rate': float(user.payment_charge) if hasattr(user, 'payment_charge') and user.payment_charge else None,
                'experience': str(user.experience) if hasattr(user, 'experience') and user.experience is not None else ''
            }
            user_list.append(user_data)
        
        response = {
            'success': True,
            'data': user_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        current_app.logger.error(f'Error in search API: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your request',
            'error': str(e)
        }), 500
