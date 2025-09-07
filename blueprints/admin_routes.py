from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.report import Report
from models.user import User
from extensions import db
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

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
        db.session.delete(user)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Error deleting user: {str(e)}'}), 500
