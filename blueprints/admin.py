from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.report import Report
from models.user import User
from models.transaction import Transaction
from models.contact_request import ContactRequest
from extensions import db
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    if user_id == current_user.id:
        return jsonify({'status': 'error', 'message': 'Cannot delete your own account'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    try:
        # Delete related messages
        from models.message import Message
        Message.query.filter(
            (Message.sender_id == user_id) | (Message.receiver_id == user_id)
        ).delete(synchronize_session=False)
        
        # Delete related reports
        from models.report import Report
        Report.query.filter(
            (Report.reporter_id == user_id) | (Report.reported_user_id == user_id)
        ).delete(synchronize_session=False)
        
        # Delete related transactions
        from models.transaction import Transaction
        Transaction.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        
        # Handle reviews - set reviewer_id to NULL or delete them
        from models.review import Review
        # Set reviewer_id to NULL if the column allows NULL
        Review.query.filter_by(reviewer_id=user_id).update({Review.reviewer_id: None}, synchronize_session=False)
        # Delete reviews where the user is being reviewed
        Review.query.filter_by(worker_id=user_id).delete(synchronize_session=False)
        
        # Handle call records - delete all calls where user is either caller or callee
        from models.Call import Call
        Call.query.filter(
            (Call.caller_id == user_id) | (Call.callee_id == user_id)
        ).delete(synchronize_session=False)
        
        # Delete user's profile photo if exists
        import os
        from flask import current_app
        if user.photo and user.photo != 'default-avatar.png':
            try:
                photo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pics', user.photo)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            except Exception as e:
                current_app.logger.error(f'Error deleting profile photo: {str(e)}')
        
        # Finally, delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'User and all related data deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.error(f'Error deleting user {user_id}: {str(e)}')
        return jsonify({'status': 'error', 'message': f'Error deleting user: {str(e)}'}), 500

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get statistics
    total_users = User.query.count()
    total_transactions = Transaction.query.count()
    total_contact_requests = ContactRequest.query.count()
    
    # Get pending reports count
    pending_reports = Report.query.filter_by(status='pending').count()
    
    # Get recent users (last 7 days)
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get recent transactions
    recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_transactions=total_transactions,
                         total_contact_requests=total_contact_requests,
                         pending_reports=pending_reports,
                         recent_users=recent_users,
                         recent_transactions=recent_transactions)

@admin_bp.route('/reported-users')
@login_required
def reported_users():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all reports with reporter and reported user details
    reports = db.session.query(
        Report,
        User.username.label('reporter_username'),
        User.full_name.label('reporter_name'),
        User.email.label('reporter_email')
    ).join(
        User, Report.reporter_id == User.id
    ).order_by(
        Report.created_at.desc()
    ).all()
    
    return render_template('admin/reported_users.html', reports=reports)

@admin_bp.route('/report/<int:report_id>/resolve', methods=['POST'])
@login_required
def resolve_report(report_id):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'status': 'error', 'message': 'Report not found'}), 404
    
    report.status = 'resolved'
    report.reviewed_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Report marked as resolved'})

@admin_bp.route('/report/<int:report_id>/delete', methods=['POST'])
@login_required
def delete_report(report_id):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'status': 'error', 'message': 'Report not found'}), 404
    
    db.session.delete(report)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Report deleted successfully'})

@admin_bp.route('/user/<int:user_id>/warn', methods=['POST'])
@login_required
def warn_user(user_id):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    # Here you would typically implement the warning logic
    # For example, increment a warning counter or send a notification
    
    return jsonify({'status': 'success', 'message': 'User has been warned'})

@admin_bp.route('/user/<int:user_id>/suspend', methods=['POST'])
@login_required
def suspend_user(user_id):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    # Suspend the user
    user.active = False
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'User has been suspended'})
