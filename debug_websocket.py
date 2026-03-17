#!/usr/bin/env python3
"""
Debug WebSocket connection issues
"""

import socketio
import time
import logging

# Enable logging
logging.basicConfig(level=logging.DEBUG)

class WebSocketDebugger:
    def __init__(self):
        self.sio = socketio.Client(logger=True, engineio_logger=True)
        self.setup_handlers()
        
    def setup_handlers(self):
        @self.sio.on('connect')
        def on_connect():
            print("✅ Connected to Socket.IO server")
            
        @self.sio.on('connect_error')
        def on_connect_error(data):
            print(f"❌ Connection error: {data}")
            
        @self.sio.on('disconnect')
        def on_disconnect():
            print("🔌 Disconnected from server")
            
    def test_transports(self):
        """Test different transport methods"""
        print("🔧 Testing Socket.IO Transports")
        print("=" * 50)
        
        # Test 1: Polling only
        print("\n1️⃣ Testing Polling Transport:")
        try:
            self.sio.connect('http://localhost:5000', transports=['polling'])
            time.sleep(1)
            if self.sio.connected:
                print("✅ Polling transport successful")
                self.sio.disconnect()
            else:
                print("❌ Polling transport failed")
        except Exception as e:
            print(f"❌ Polling error: {e}")
            
        time.sleep(2)
        
        # Test 2: WebSocket only
        print("\n2️⃣ Testing WebSocket Transport:")
        try:
            self.sio.connect('http://localhost:5000', transports=['websocket'])
            time.sleep(1)
            if self.sio.connected:
                print("✅ WebSocket transport successful")
                self.sio.disconnect()
            else:
                print("❌ WebSocket transport failed")
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
            
        time.sleep(2)
        
        # Test 3: Both (with upgrade)
        print("\n3️⃣ Testing Both Transports (with upgrade):")
        try:
            self.sio.connect('http://localhost:5000', transports=['polling', 'websocket'])
            time.sleep(2)
            if self.sio.connected:
                print("✅ Both transports successful")
                self.sio.disconnect()
            else:
                print("❌ Both transports failed")
        except Exception as e:
            print(f"❌ Both transports error: {e}")

if __name__ == '__main__':
    debugger = WebSocketDebugger()
    debugger.test_transports()
