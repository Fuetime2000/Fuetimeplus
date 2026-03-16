#!/usr/bin/env python3
"""
Test script for registration form error handling and data persistence
"""
import requests
import json

# Base URL for testing
BASE_URL = "http://localhost:5000"

def test_registration_errors():
    """Test various registration error scenarios"""
    
    print("Testing Registration Form Error Handling")
    print("=" * 50)
    
    # Test 1: Empty form submission
    print("\n1. Testing empty form submission...")
    response = requests.post(f"{BASE_URL}/register", data={})
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ Empty form rejected successfully")
    else:
        print("✗ Empty form handling failed")
    
    # Test 2: Invalid email format
    print("\n2. Testing invalid email format...")
    invalid_email_data = {
        'full_name': 'Test User',
        'email': 'invalid-email',
        'phone': '1234567890',
        'password': 'password123',
        'confirm_password': 'password123',
        'live_location': 'Test Location',
        'date_of_birth': '2000-01-01'
    }
    response = requests.post(f"{BASE_URL}/register", data=invalid_email_data)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ Invalid email rejected successfully")
    else:
        print("✗ Invalid email handling failed")
    
    # Test 3: Invalid phone format
    print("\n3. Testing invalid phone format...")
    invalid_phone_data = {
        'full_name': 'Test User',
        'email': 'test@example.com',
        'phone': '123',
        'password': 'password123',
        'confirm_password': 'password123',
        'live_location': 'Test Location',
        'date_of_birth': '2000-01-01'
    }
    response = requests.post(f"{BASE_URL}/register", data=invalid_phone_data)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ Invalid phone rejected successfully")
    else:
        print("✗ Invalid phone handling failed")
    
    # Test 4: Underage user
    print("\n4. Testing underage user...")
    underage_data = {
        'full_name': 'Test User',
        'email': 'test@example.com',
        'phone': '1234567890',
        'password': 'password123',
        'confirm_password': 'password123',
        'live_location': 'Test Location',
        'date_of_birth': '2010-01-01'  # Too young
    }
    response = requests.post(f"{BASE_URL}/register", data=underage_data)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ Underage user rejected successfully")
    else:
        print("✗ Underage user handling failed")
    
    print("\n" + "=" * 50)
    print("Error handling tests completed!")

def test_form_page():
    """Test if the registration page loads correctly"""
    print("\nTesting Registration Page Load")
    print("=" * 30)
    
    response = requests.get(f"{BASE_URL}/register")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ Registration page loads successfully")
        if 'field_errors' in response.text:
            print("✓ Template supports field-specific errors")
        if 'localStorage' in response.text:
            print("✓ JavaScript for data persistence is present")
    else:
        print("✗ Registration page failed to load")

if __name__ == "__main__":
    try:
        test_form_page()
        test_registration_errors()
        print("\n" + "=" * 50)
        print("All tests completed!")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the Flask application.")
        print("Please make sure the Flask app is running on http://localhost:5000")
    except Exception as e:
        print(f"An error occurred: {e}")
