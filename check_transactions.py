from app import app, db
from models.transaction import Transaction
from models.user import User

def check_transactions():
    with app.app_context():
        # Get total number of transactions
        total_transactions = Transaction.query.count()
        print(f"Total transactions in database: {total_transactions}")
        
        # Get the first few transactions if they exist
        if total_transactions > 0:
            print("\nSample transactions:")
            transactions = Transaction.query.limit(5).all()
            for i, txn in enumerate(transactions, 1):
                print(f"\nTransaction {i}:")
                print(f"  ID: {txn.id}")
                print(f"  User ID: {txn.user_id}")
                print(f"  Amount: {txn.amount}")
                print(f"  Type: {txn.transaction_type}")
                print(f"  Description: {txn.description}")
                print(f"  Created At: {txn.created_at}")
        
        # Check if there are any users with wallet balances
        users_with_balance = User.query.filter(User.wallet_balance > 0).count()
        print(f"\nUsers with wallet balance > 0: {users_with_balance}")

if __name__ == "__main__":
    check_transactions()
