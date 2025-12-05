import os
import json
from flask import current_app

# Firebase Admin SDK will be initialized when credentials are provided
firebase_admin = None
messaging = None

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    global firebase_admin, messaging
    
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging as fcm_messaging
        
        # Check if already initialized
        if firebase_admin._apps:
            current_app.logger.info("Firebase already initialized")
            messaging = fcm_messaging
            return True
        
        # Get Firebase credentials from environment or config
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            messaging = fcm_messaging
            current_app.logger.info("Firebase initialized successfully from file")
            return True
        
        # Try to get credentials from environment variable (JSON string)
        cred_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
        if cred_json:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            messaging = fcm_messaging
            current_app.logger.info("Firebase initialized successfully from JSON")
            return True
        
        current_app.logger.warning("Firebase credentials not found. Emergency alerts will not work.")
        return False
        
    except ImportError:
        current_app.logger.error("firebase-admin package not installed. Run: pip install firebase-admin")
        return False
    except Exception as e:
        current_app.logger.error(f"Error initializing Firebase: {str(e)}")
        return False


def send_fcm_notification(device_token, title, body, data=None):
    """
    Send FCM notification to a device
    
    Args:
        device_token: FCM device token
        title: Notification title
        body: Notification body
        data: Additional data payload (dict)
    
    Returns:
        tuple: (success: bool, message_id or error: str)
    """
    global messaging
    
    if not messaging:
        if not initialize_firebase():
            return False, "Firebase not initialized"
    
    try:
        from firebase_admin import messaging as fcm_messaging
        
        # Build notification
        notification = fcm_messaging.Notification(
            title=title,
            body=body
        )
        
        # Build Android config for high priority
        android_config = fcm_messaging.AndroidConfig(
            priority='high',
            notification=fcm_messaging.AndroidNotification(
                sound='default',
                priority='high',
                channel_id='emergency_alerts'
            )
        )
        
        # Build message
        message = fcm_messaging.Message(
            notification=notification,
            data=data or {},
            token=device_token,
            android=android_config
        )
        
        # Send message
        response = fcm_messaging.send(message)
        current_app.logger.info(f"FCM notification sent successfully: {response}")
        return True, response
        
    except Exception as e:
        error_msg = str(e)
        current_app.logger.error(f"Error sending FCM notification: {error_msg}")
        return False, error_msg


def send_emergency_alert(device_token, alert_data):
    """
    Send emergency alert notification
    
    Args:
        device_token: FCM device token
        alert_data: Dictionary containing alert information
    
    Returns:
        tuple: (success: bool, message_id or error: str)
    """
    reason = alert_data.get('reason', 'EMERGENCY')
    device_name = alert_data.get('deviceName', 'Unknown Device')
    
    # Map reason to user-friendly message
    reason_messages = {
        'FALL_DETECTED': 'Fall Detected!',
        'SOS_BUTTON': 'SOS Alert!',
        'PANIC_BUTTON': 'Panic Button Pressed!',
        'EMERGENCY': 'Emergency Alert!'
    }
    
    title = reason_messages.get(reason, 'Emergency Alert!')
    body = f"{device_name} needs help! Tap to view details."
    
    # Prepare data payload
    data = {
        'type': 'emergency_alert',
        'reason': reason,
        'latitude': str(alert_data.get('latitude', '')),
        'longitude': str(alert_data.get('longitude', '')),
        'accuracy': str(alert_data.get('accuracy', '')),
        'batteryLevel': str(alert_data.get('batteryLevel', '')),
        'timestamp': str(alert_data.get('timestamp', '')),
        'message': alert_data.get('message', ''),
        'deviceName': device_name
    }
    
    return send_fcm_notification(device_token, title, body, data)
