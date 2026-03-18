#!/usr/bin/env python3
"""
Test script to verify that messages are sent only to specific users
and not broadcast to all users.
"""

import asyncio
import socketio
import json
import time
from datetime import datetime

# Create Socket.IO clients
sio = socketio.AsyncClient()

# Test data
test_users = {
    'user1': {'id': 1, 'token': 'test_token_1'},
    'user2': {'id': 2, 'token': 'test_token_2'},
    'user3': {'id': 3, 'token': 'test_token_3'}
}

message_received = {}

async def connect_user(user_name):
    """Connect a user and track their received messages"""
    user_info = test_users[user_name]
    message_received[user_name] = []
    
    @sio.on('connect')
    def on_connect():
        print(f"✅ {user_name} connected successfully")
    
    @sio.on('new_message')
    def on_new_message(data):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] 📨 {user_name} received message from user {data['sender_id']}: {data['content']}")
        message_received[user_name].append(data)
    
    @sio.on('error')
    def on_error(data):
        print(f"❌ {user_name} received error: {data}")
    
    # Connect with user authentication
    await sio.connect(
        'http://localhost:5000',
        auth={'user_id': user_info['id'], 'token': user_info['token']},
        namespaces=['/ws']
    )

async def send_message(sender_name, recipient_id, content):
    """Send a message from one user to another"""
    print(f"📤 {sender_name} sending message to user {recipient_id}: {content}")
    
    await sio.emit('message', {
        'recipient_id': recipient_id,
        'content': content
    }, namespace='/ws')
    
    # Wait a bit for message processing
    await asyncio.sleep(0.5)

async def test_message_routing():
    """Test that messages are routed correctly to specific users only"""
    print("🧪 Starting message routing test...")
    print("=" * 60)
    
    try:
        # Connect all test users
        print("Connecting test users...")
        await connect_user('user1')
        await asyncio.sleep(0.5)
        
        # Test 1: Send message from user1 to user2
        print("\n📋 Test 1: user1 sends message to user2")
        await send_message('user1', 2, "Hello user2! This message should only go to you.")
        
        # Wait for message delivery
        await asyncio.sleep(1)
        
        # Check results
        print("\n📊 Results:")
        user1_received = len(message_received.get('user1', []))
        user2_received = len(message_received.get('user2', []))
        user3_received = len(message_received.get('user3', []))
        
        print(f"   user1 received: {user1_received} messages")
        print(f"   user2 received: {user2_received} messages") 
        print(f"   user3 received: {user3_received} messages")
        
        # Verify expected behavior
        if user1_received == 1 and user2_received == 1 and user3_received == 0:
            print("✅ PASS: Message routed correctly - only sender and recipient received it")
        else:
            print("❌ FAIL: Message routing incorrect")
            print(f"   Expected: user1=1, user2=1, user3=0")
            print(f"   Actual: user1={user1_received}, user2={user2_received}, user3={user3_received}")
        
        # Test 2: Send message from user1 to user3
        print("\n📋 Test 2: user1 sends message to user3")
        await send_message('user1', 3, "Hi user3! This should only go to you.")
        
        # Wait for message delivery
        await asyncio.sleep(1)
        
        # Check results
        user1_received = len(message_received.get('user1', []))
        user2_received = len(message_received.get('user2', []))
        user3_received = len(message_received.get('user3', []))
        
        print("\n📊 Results:")
        print(f"   user1 received: {user1_received} messages")
        print(f"   user2 received: {user2_received} messages") 
        print(f"   user3 received: {user3_received} messages")
        
        if user1_received == 2 and user2_received == 1 and user3_received == 1:
            print("✅ PASS: Message routed correctly - only sender and recipient received it")
        else:
            print("❌ FAIL: Message routing incorrect")
            print(f"   Expected: user1=2, user2=1, user3=1")
            print(f"   Actual: user1={user1_received}, user2={user2_received}, user3={user3_received}")
        
        print("\n" + "=" * 60)
        print("🏁 Test completed!")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
    
    finally:
        await sio.disconnect()

if __name__ == '__main__':
    print("🚀 Starting message routing test...")
    print("Make sure your Flask app is running on localhost:5000")
    print("Press Ctrl+C to stop the test\n")
    
    try:
        asyncio.run(test_message_routing())
    except KeyboardInterrupt:
        print("\n👋 Test stopped by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
