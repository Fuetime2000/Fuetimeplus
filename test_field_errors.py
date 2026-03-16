#!/usr/bin/env python3
"""
Advanced test script for field-specific error messages in registration form
"""
import requests
from bs4 import BeautifulSoup

# Base URL for testing
BASE_URL = "http://localhost:5000"

def test_field_specific_errors():
    """Test that field-specific errors are displayed correctly"""
    
    print("Testing Field-Specific Error Messages")
    print("=" * 50)
    
    # Test 1: Missing required fields
    print("\n1. Testing missing required fields...")
    response = requests.post(f"{BASE_URL}/register", data={
        'full_name': 'Test User',
        'email': '',  # Missing email
        'phone': '',  # Missing phone
        'password': 'password123',
        'live_location': 'Test Location'
    })
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if field-specific error messages are present
        email_error = soup.find('input', {'name': 'email'})
        phone_error = soup.find('input', {'name': 'phone'})
        
        if email_error and 'is-invalid' in email_error.get('class', []):
            print("✓ Email field shows error state")
        else:
            print("✗ Email field does not show error state")
            
        if phone_error and 'is-invalid' in phone_error.get('class', []):
            print("✓ Phone field shows error state")
        else:
            print("✗ Phone field does not show error state")
    
    # Test 2: Invalid email format
    print("\n2. Testing invalid email format error...")
    response = requests.post(f"{BASE_URL}/register", data={
        'full_name': 'Test User',
        'email': 'invalid-email-format',
        'phone': '1234567890',
        'password': 'password123',
        'live_location': 'Test Location',
        'date_of_birth': '2000-01-01'
    })
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        email_input = soup.find('input', {'name': 'email'})
        
        if email_input and 'is-invalid' in email_input.get('class', []):
            print("✓ Invalid email field shows error state")
            
            # Check for specific error message
            error_div = email_input.find_next('div', class_='invalid-feedback')
            if error_div and 'Invalid email format' in error_div.text:
                print("✓ Specific email error message displayed")
            else:
                print("✗ Specific email error message not found")
        else:
            print("✗ Invalid email field does not show error state")
    
    # Test 3: Invalid phone format
    print("\n3. Testing invalid phone format error...")
    response = requests.post(f"{BASE_URL}/register", data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'phone': '12345',  # Invalid phone
        'password': 'password123',
        'live_location': 'Test Location',
        'date_of_birth': '2000-01-01'
    })
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        phone_input = soup.find('input', {'name': 'phone'})
        
        if phone_input and 'is-invalid' in phone_input.get('class', []):
            print("✓ Invalid phone field shows error state")
            
            # Check for specific error message
            error_div = phone_input.find_next('div', class_='invalid-feedback')
            if error_div and 'Invalid phone number' in error_div.text:
                print("✓ Specific phone error message displayed")
            else:
                print("✗ Specific phone error message not found")
        else:
            print("✗ Invalid phone field does not show error state")
    
    # Test 4: Data persistence (form data retained)
    print("\n4. Testing form data persistence...")
    test_data = {
        'full_name': 'John Doe',
        'email': 'john@example.com',
        'phone': '9876543210',
        'password': 'password123',
        'live_location': 'Test Village',
        'date_of_birth': '1990-01-01'
    }
    
    response = requests.post(f"{BASE_URL}/register", data=test_data)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if form data is retained in the form
        full_name_input = soup.find('input', {'name': 'full_name'})
        email_input = soup.find('input', {'name': 'email'})
        phone_input = soup.find('input', {'name': 'phone'})
        
        data_retained = True
        
        if full_name_input and full_name_input.get('value') != 'John Doe':
            print("✗ Full name data not retained")
            data_retained = False
        else:
            print("✓ Full name data retained")
            
        if email_input and email_input.get('value') != 'john@example.com':
            print("✗ Email data not retained")
            data_retained = False
        else:
            print("✓ Email data retained")
            
        if phone_input and phone_input.get('value') != '9876543210':
            print("✗ Phone data not retained")
            data_retained = False
        else:
            print("✓ Phone data retained")
        
        if data_retained:
            print("✓ Form data persistence working correctly")
        else:
            print("✗ Form data persistence has issues")

if __name__ == "__main__":
    try:
        test_field_specific_errors()
        print("\n" + "=" * 50)
        print("Field-specific error tests completed!")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the Flask application.")
        print("Please make sure the Flask app is running on http://localhost:5000")
    except Exception as e:
        print(f"An error occurred: {e}")
