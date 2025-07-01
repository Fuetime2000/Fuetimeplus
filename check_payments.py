from app import app, db
from models.user import User

with app.app_context():
    users = User.query.filter(User.payment_charge.isnot(None)).all()
    print("ID\tPayment Charge\tPayment Type")
    print("-" * 40)
    for user in users:
        print(f"{user.id}\t{user.payment_charge}\t\t{user.payment_type}")
