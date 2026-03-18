#!/usr/bin/env python3
"""
Test to verify that messages are only sent to specific users after the final fix.
This simulates the HTTP route message sending that the Flutter app uses.
"""

import requests
import socketio
import time
import threading
from datetime import datetime

# Test configuration
BASE_URL = 'http://localhost:5000'
TEST_USERS = {
    'user1': {'id': 1, 'token': 'test_token_1'},
    'user2': {'id': 2, 'token': 'test_token_2'}, 
    'user3': {'id': 3, 'token': 'test_token_3'}
}

class MessageReceiver:
    def __init__(self, user_name, user_id):
        self.user_name = user_name
        self.user_id = user_id
        self.messages_received = []
        self.sio = socketio.Client(logger=False, engineio_logger=False)
        
        # Set up event handlers
        @self.sio.on('connect')
        def on_connect():
            print(f"✅ {self.user_name} connected")
            
        @self.sio.on('new_message')
        def on_new_message(data):
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] 📨 {self.user_name} received message: {data.get('content', 'No content')} from user {data.get('sender_id')}")
            self.messages_received.append(data)
            
        @self.sio.on('disconnect')
        def on_disconnect():
            print(f"❌ {self.user_name} disconnected")
            
        @self.sio.on('error')
        def on_error(data):
            print(f"❌ {self.user_name} error: {data}")
    
    def connect(self):
        """Connect to Socket.IO server"""
        try:
            self.sio.connect(BASE_URL, auth={'user_id': self.user_id})
            return True
        except Exception as e:
            print(f"❌ {self.user_name} connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Socket.IO server"""
        self.sio.disconnect()

def test_http_message_routing():
    """Test that HTTP POST /chat routes only send messages to specific users"""
    print("🧪 Testing HTTP Message Routing (Flutter App Simulation)")
    print("=" * 60)
    
    # Create message receivers for each user
    receivers = []
    for user_name, user_info in TEST_USERS.items():
        receiver = MessageReceiver(user_name, user_info['id'])
        receivers.append(receiver)
    
    try:
        # Connect all users to Socket.IO
        print("🔌 Connecting all users to Socket.IO...")
        for receiver in receivers:
            if not receiver.connect():
                print(f"❌ Failed to connect {receiver.user_name}")
                return False
            time.sleep(0.5)
        
        print("✅ All users connected")
        time.sleep(1)
        
        # Test 1: Send message from user1 to user2 via HTTP POST
        print("\n📤 Test 1: Sending message from user1 to user2 via HTTP POST")
        
        # Simulate Flutter app sending HTTP POST request
        message_data = {
            'content': 'Hello user2! This should only go to you and user1.',
            'recipient_id': 2
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/chat/2",
                data=message_data,
                timeout=5
            )
            print(f"📡 HTTP POST /chat/2 response: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTP request failed: {e}")
            return False
        
        # Wait for Socket.IO messages to be delivered
        time.sleep(2)
        
        # Check who received messages
        print("\n📊 Message Delivery Results:")
        for receiver in receivers:
            count = len(receiver.messages_received)
            print(f"   {receiver.user_name}: {count} message(s)")
            
            # Show message details
            for msg in receiver.messages_received:
                print(f"      - From: {msg.get('sender_id')}, To: {msg.get('recipient_id')}, Content: {msg.get('content')[:50]}...")
        
        # Verify expected behavior
        user1_count = len(receivers[0].messages_received)  # user1 (sender)
        user2_count = len(receivers[1].messages_received)  # user2 (recipient)
        user3_count = len(receivers[2].messages_received)  # user3 (other user)
        
        print(f"\n🎯 Expected: user1=1, user2=1, user3=0")
        print(f"📈 Actual:   user1={user1_count}, user2={user2_count}, user3={user3_count}")
        
        if user1_count == 1 and user2_count == 1 and user3_count == 0:
            print("✅ PASS: Message routed correctly!")
        else:
            print("❌ FAIL: Message routing incorrect!")
            return False
        
        # Clear messages for next test
        for receiver in receivers:
            receiver.messages_received.clear()
        
        # Test 2: Send message from user1 to user3
        print("\n📤 Test 2: Sending message from user1 to user3 via HTTP POST")
        
        message_data2 = {
            'content': 'Hi user3! This should only go to you and user1.',
            'recipient_id': 3
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/chat/3",
                data=message_data2,
                timeout=5
            )
            print(f"📡 HTTP POST /chat/3 response: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTP request failed: {e}")
            return False
        
        # Wait for Socket.IO messages
        time.sleep(2)
        
        # Check results again
        print("\n📊 Message Delivery Results:")
        for receiver in receivers:
            count = len(receiver.messages_received)
            print(f"   {receiver.user_name}: {count} message(s)")
        
        user1_count = len(receivers[0].messages_received)  # user1 (sender)
        user2_count = len(receivers[1].messages_received)  # user2 (not involved)
        user3_count = len(receivers[2].messages_received)  # user3 (recipient)
        
        print(f"\n🎯 Expected: user1=1, user2=0, user3=1")
        print(f"📈 Actual:   user1={user1_count}, user2={user2_count}, user3={user3_count}")
        
        if user1_count == 1 and user2_count == 0 and user3_count == 1:
            print("✅ PASS: Second message routed correctly!")
            return True
        else:
            print("❌ FAIL: Second message routing incorrect!")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
        
    finally:
        # Disconnect all users
        print("\n🔌 Disconnecting all users...")
        for receiver in receivers:
            receiver.disconnect()

if __name__ == '__main__':
    print("🚀 HTTP Message Routing Test")
    print("This simulates how your Flutter app sends messages")
    print("Make sure your Flask app is running on localhost:5000\n")
    
    try:
        success = test_http_message_routing()
        if success:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Messages are only sent to intended recipients")
            print("✅ No more broadcasting to all users")
            print("\n🚀 Your Flutter app chat should now work correctly!")
        else:
            print("\n❌ TESTS FAILED")
            print("There are still message routing issues")
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test stopped by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        exit(1)
