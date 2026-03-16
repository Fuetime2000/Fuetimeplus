#!/usr/bin/env python3
"""
Test script to verify WebSocket connections are working properly
"""

import socketio
import time
import threading
from urllib.parse import urljoin

class WebSocketTest:
    def __init__(self):
        self.sio = socketio.Client()
        self.connected = False
        self.errors = []
        self.messages = []
        
        # Set up event handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('connect_error', self.on_connect_error)
        self.sio.on('status', self.on_status)
        self.sio.on('message', self.on_message)
        
    def on_connect(self):
        """Handle successful connection"""
        self.connected = True
        print("✅ Successfully connected to WebSocket server")
        
    def on_disconnect(self):
        """Handle disconnection"""
        self.connected = False
        print("❌ Disconnected from WebSocket server")
        
    def on_connect_error(self, error):
        """Handle connection errors"""
        self.errors.append(str(error))
        print(f"❌ Connection error: {error}")
        
    def on_status(self, data):
        """Handle status messages"""
        print(f"📊 Status update: {data}")
        self.messages.append(data)
        
    def on_message(self, data):
        """Handle general messages"""
        print(f"💬 Message: {data}")
        self.messages.append(data)
    
    def test_connection(self, server_url='http://localhost:5000'):
        """Test WebSocket connection"""
        print(f"🚀 Testing WebSocket connection to {server_url}")
        
        try:
            # Connect to the server using polling only for stability
            self.sio.connect(server_url, transports=['polling'])
            
            # Wait a bit for connection to establish
            time.sleep(2)
            
            was_connected = self.connected
            
            if was_connected:
                print("✅ Connection successful!")
                
                # Test sending a message
                self.sio.emit('join', {'room': 'test_room'})
                time.sleep(1)
                
                # Test another event
                self.sio.emit('message', {'content': 'Test message from WebSocket test'})
                time.sleep(1)
                
            else:
                print("❌ Connection failed")
                return False
                
        except Exception as e:
            print(f"❌ Exception during connection test: {e}")
            self.errors.append(str(e))
            return False
        finally:
            # Clean up
            try:
                if self.sio.connected:
                    self.sio.disconnect()
                    time.sleep(1)
            except:
                pass
        
        # Report results
        print(f"\n📋 Test Results:")
        print(f"   Was connected: {was_connected}")
        print(f"   Errors: {len(self.errors)}")
        print(f"   Messages received: {len(self.messages)}")
        
        if self.errors:
            print(f"   Errors list: {self.errors}")
        
        return was_connected and len(self.errors) == 0

def main():
    """Main test function"""
    print("🔧 WebSocket Connection Test")
    print("=" * 50)
    
    tester = WebSocketTest()
    success = tester.test_connection()
    
    if success:
        print("\n🎉 WebSocket test PASSED!")
        return 0
    else:
        print("\n💥 WebSocket test FAILED!")
        return 1

if __name__ == '__main__':
    exit(main())
