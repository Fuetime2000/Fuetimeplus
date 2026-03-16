#!/usr/bin/env python3
"""
Test script to verify Socket.IO connection to /ws namespace with authentication
"""

import socketio
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocketIOClientWithAuth:
    def __init__(self):
        self.sio = socketio.AsyncClient(logger=True, engineio_logger=True)
        self.connected = False
        
        # Register event handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('connect_error', self.on_connect_error)
        self.sio.on('status', self.on_status)
        self.sio.on('error', self.on_error)
        
    async def on_connect(self):
        logger.info("Connected to Socket.IO server!")
        self.connected = True
        
    async def on_disconnect(self):
        logger.info("Disconnected from Socket.IO server")
        self.connected = False
        
    async def on_connect_error(self, data):
        logger.error(f"Connection error: {data}")
        self.connected = False
        
    async def on_status(self, data):
        logger.info(f"Status update: {data}")
        
    async def on_error(self, data):
        logger.error(f"Socket.IO error: {data}")
        
    async def connect_to_ws_namespace(self, url='http://localhost:5000', user_id='2', token=None):
        try:
            logger.info(f"Attempting to connect to {url}/ws with user_id={user_id}")
            
            # Build URL with query parameters
            socketio_url = f"{url}/socket.io"
            if token:
                socketio_url += f"?token={token}&user_id={user_id}"
            else:
                socketio_url += f"?user_id={user_id}"
            
            logger.info(f"Connecting to: {socketio_url}")
            
            # Connect with authentication parameters
            await self.sio.connect(
                socketio_url,
                namespaces=['/ws'],
                transports=['polling', 'websocket']
            )
            
            # Wait a bit to see if connection succeeds
            await asyncio.sleep(2)
            
            if self.connected:
                logger.info("✅ Socket.IO connection successful!")
                return True
            else:
                logger.error("❌ Socket.IO connection failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception during connection: {e}")
            return False
        finally:
            if self.connected:
                await self.sio.disconnect()

async def main():
    # Test without token first
    client = SocketIOClientWithAuth()
    success = await client.connect_to_ws_namespace()
    
    if success:
        print("\n✅ Socket.IO /ws namespace is working!")
    else:
        print("\n❌ Socket.IO /ws namespace has issues")
        print("Check the server logs for more details")

if __name__ == '__main__':
    asyncio.run(main())
