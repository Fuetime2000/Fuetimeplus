#!/usr/bin/env python3
from app import app
from models.user import User

def check_user_count():
    with app.app_context():
        total_users = User.query.count()
        active_users = User.query.filter_by(active=True).count()
        verified_users = User.query.filter_by(verified=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        worker_users = User.query.filter_by(user_type='worker').count()
        client_users = User.query.filter_by(user_type='client').count()
        
        print(f"Total registered users: {total_users}")
        print(f"Active users: {active_users}")
        print(f"Verified users: {verified_users}")
        print(f"Admin users: {admin_users}")
        print(f"Worker users: {worker_users}")
        print(f"Client users: {client_users}")
        
        # Show recent users
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        print("\nRecent 5 users:")
        for user in recent_users:
            print(f"  - {user.full_name} ({user.email}) - {user.user_type} - Created: {user.created_at}")

if __name__ == "__main__":
    check_user_count()
