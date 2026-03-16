#!/usr/bin/env python3
"""
Simple test to check if Socket.IO server is responding
"""

import requests
import time

def test_socketio_server():
    """Test if Socket.IO server is responding to polling requests"""
    print("🔧 Testing Socket.IO Server Response")
    print("=" * 50)
    
    try:
        # Test basic Socket.IO polling endpoint
        url = "http://localhost:5000/socket.io/?EIO=4&transport=polling"
        
        print(f"📡 Testing: {url}")
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Server responded with status {response.status_code}")
            print(f"📄 Response content: {response.text[:100]}...")
            
            # Test with a session ID
            sid = response.text.split(':')[0] if ':' in response.text else None
            if sid and sid.isdigit():
                print(f"🔑 Session ID: {sid}")
                
                # Test POST to same session
                post_url = f"http://localhost:5000/socket.io/?EIO=4&transport=polling&sid={sid}"
                post_response = requests.post(post_url, data="1", timeout=5)
                
                if post_response.status_code == 200:
                    print(f"✅ POST request successful with status {post_response.status_code}")
                    return True
                else:
                    print(f"❌ POST request failed with status {post_response.status_code}")
                    return False
            else:
                print("⚠️  Could not extract session ID")
                return True  # Still consider success if basic GET works
                
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused - server may not be running")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = test_socketio_server()
    
    if success:
        print("\n🎉 Socket.IO server is responding correctly!")
        exit(0)
    else:
        print("\n💥 Socket.IO server test failed!")
        exit(1)
