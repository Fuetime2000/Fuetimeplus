#!/usr/bin/env python3
"""
Test script for deeplink functionality
"""
import requests
import json

# Base URL for testing
BASE_URL = "http://localhost:5000"

def test_deeplinks():
    """Test various deeplink scenarios"""
    
    print("Testing Deeplink Functionality")
    print("=" * 50)
    
    # Test 1: Base deeplink
    print("\n1. Testing base deeplink...")
    response = requests.get(f"{BASE_URL}/deeplink")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ Base deeplink works")
    else:
        print("✗ Base deeplink failed")
    
    # Test 2: Profile deeplink (web browser)
    print("\n2. Testing profile deeplink (web browser)...")
    response = requests.get(f"{BASE_URL}/deeplink/profile/123")
    print(f"Status Code: {response.status_code}")
    print(f"Redirect Location: {response.headers.get('Location', 'No redirect')}")
    if response.status_code in [200, 302]:
        print("✓ Profile deeplink works")
    else:
        print("✗ Profile deeplink failed")
    
    # Test 3: Profile deeplink (mobile app simulation)
    print("\n3. Testing profile deeplink (mobile app)...")
    headers = {'User-Agent': 'FuetimeApp/1.0 (Capacitor)'}
    response = requests.get(f"{BASE_URL}/deeplink/profile/123", headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get('status') == 'redirect':
                print("✓ Mobile app profile deeplink works")
            else:
                print("✗ Mobile app profile deeplink response invalid")
        except:
            print("✗ Mobile app profile deeplink not JSON")
    else:
        print("✗ Mobile app profile deeplink failed")
    
    # Test 4: Job deeplink (mobile app)
    print("\n4. Testing job deeplink (mobile app)...")
    headers = {'User-Agent': 'FuetimeApp/1.0 (Capacitor)'}
    response = requests.get(f"{BASE_URL}/deeplink/job/456", headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get('status') == 'redirect':
                print("✓ Mobile app job deeplink works")
            else:
                print("✗ Mobile app job deeplink response invalid")
        except:
            print("✗ Mobile app job deeplink not JSON")
    else:
        print("✗ Mobile app job deeplink failed")
    
    # Test 5: Register deeplink (mobile app)
    print("\n5. Testing register deeplink (mobile app)...")
    headers = {'User-Agent': 'FuetimeApp/1.0 (Capacitor)'}
    response = requests.get(f"{BASE_URL}/deeplink/register", headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get('status') == 'redirect':
                print("✓ Mobile app register deeplink works")
            else:
                print("✗ Mobile app register deeplink response invalid")
        except:
            print("✗ Mobile app register deeplink not JSON")
    else:
        print("✗ Mobile app register deeplink failed")
    
    # Test 6: Login deeplink (mobile app)
    print("\n6. Testing login deeplink (mobile app)...")
    headers = {'User-Agent': 'FuetimeApp/1.0 (Capacitor)'}
    response = requests.get(f"{BASE_URL}/deeplink/login", headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get('status') == 'redirect':
                print("✓ Mobile app login deeplink works")
            else:
                print("✗ Mobile app login deeplink response invalid")
        except:
            print("✗ Mobile app login deeplink not JSON")
    else:
        print("✗ Mobile app login deeplink failed")
    
    # Test 7: Message deeplink (mobile app)
    print("\n7. Testing message deeplink (mobile app)...")
    headers = {'User-Agent': 'FuetimeApp/1.0 (Capacitor)'}
    response = requests.get(f"{BASE_URL}/deeplink/message/789", headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get('status') == 'redirect':
                print("✓ Mobile app message deeplink works")
            else:
                print("✗ Mobile app message deeplink response invalid")
        except:
            print("✗ Mobile app message deeplink not JSON")
    else:
        print("✗ Mobile app message deeplink failed")
    
    # Test 8: Unknown deeplink (mobile app)
    print("\n8. Testing unknown deeplink (mobile app)...")
    headers = {'User-Agent': 'FuetimeApp/1.0 (Capacitor)'}
    response = requests.get(f"{BASE_URL}/deeplink/unknown/path", headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 400:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get('status') == 'error':
                print("✓ Unknown deeplink properly handled")
            else:
                print("✗ Unknown deeplink response invalid")
        except:
            print("✗ Unknown deeplink not JSON")
    else:
        print("✗ Unknown deeplink handling failed")
    
    # Test 9: Test page accessibility
    print("\n9. Testing deeplink test page...")
    response = requests.get(f"{BASE_URL}/test-deeplink")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ Deeplink test page accessible")
    else:
        print("✗ Deeplink test page not accessible")

def test_capacitor_config():
    """Test if Capacitor configuration is valid"""
    print("\n" + "=" * 50)
    print("Testing Capacitor Configuration")
    print("=" * 30)
    
    try:
        with open('capacitor.config.json', 'r') as f:
            config = json.load(f)
        
        print("✓ Capacitor config file is valid JSON")
        
        # Check required fields
        required_fields = ['appId', 'appName', 'webDir', 'urlHandlers']
        for field in required_fields:
            if field in config:
                print(f"✓ {field} present")
            else:
                print(f"✗ {field} missing")
        
        # Check urlHandlers
        if 'urlHandlers' in config:
            handlers = config['urlHandlers']
            fuetime_handler = any('fuetime://' in handler.get('url', '') for handler in handlers)
            if fuetime_handler:
                print("✓ fuetime:// deeplink handler configured")
            else:
                print("✗ fuetime:// deeplink handler not found")
        
    except FileNotFoundError:
        print("✗ capacitor.config.json not found")
    except json.JSONDecodeError:
        print("✗ capacitor.config.json is invalid JSON")
    except Exception as e:
        print(f"✗ Error reading capacitor.config.json: {e}")

if __name__ == "__main__":
    try:
        test_deeplinks()
        test_capacitor_config()
        print("\n" + "=" * 50)
        print("Deeplink tests completed!")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the Flask application.")
        print("Please make sure the Flask app is running on http://localhost:5000")
    except Exception as e:
        print(f"An error occurred: {e}")
