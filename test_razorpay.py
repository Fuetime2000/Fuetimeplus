import os
import sys
import hmac
import hashlib
from dotenv import load_dotenv

# Set console output encoding to UTF-8
if sys.stdout.encoding != 'utf-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load environment variables
load_dotenv()

def test_razorpay_config():
    """Test Razorpay configuration and signature verification."""
    # Get configuration
    key_id = os.getenv('RAZORPAY_KEY_ID')
    key_secret = os.getenv('RAZORPAY_KEY_SECRET')
    
    print("\n=== Razorpay Configuration Test ===")
    print(f"Key ID: {key_id}")
    print(f"Key Secret: {'*' * (len(key_secret) - 4) + key_secret[-4:] if key_secret else 'Not set'}")
    
    if not all([key_id, key_secret]):
        print("\n❌ Error: RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET not set in .env")
        return False
    
    # Test data (you can replace with actual test data from Razorpay)
    test_order_id = "order_test123"
    test_payment_id = "pay_test123"
    
    # Generate a test signature
    payload = f"{test_order_id}|{test_payment_id}"
    generated_signature = hmac.new(
        key_secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print("\n=== Signature Test ===")
    print(f"Order ID: {test_order_id}")
    print(f"Payment ID: {test_payment_id}")
    print(f"Generated Signature: {generated_signature}")
    
    # Test signature verification
    try:
        # This is the same signature we just generated, so it should verify
        is_valid = hmac.compare_digest(generated_signature, generated_signature)
        print("\n[SUCCESS] Signature verification test: PASSED" if is_valid else "\n[ERROR] Signature verification test: FAILED")
        return is_valid
    except Exception as e:
        print(f"\n[ERROR] During signature verification: {str(e)}")
        return False

if __name__ == "__main__":
    test_razorpay_config()
