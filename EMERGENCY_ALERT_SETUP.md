# Emergency Alert System - Setup Guide

## 📋 Overview

This document provides complete setup instructions for the Device-to-Device Emergency Alert System for Lairy.

## 🔧 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `firebase-admin>=6.2.0` - Firebase Admin SDK for push notifications
- All other required dependencies

### 2. Firebase Setup

#### A. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add Project" or select existing project
3. Follow the setup wizard

#### B. Enable Firebase Cloud Messaging (FCM)

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Navigate to **Cloud Messaging** tab
3. Note your **Server Key** and **Sender ID**

#### C. Generate Service Account Key

1. In Firebase Console, go to **Project Settings** → **Service Accounts**
2. Click **Generate New Private Key**
3. Download the JSON file (e.g., `firebase-credentials.json`)
4. **Keep this file secure!** Never commit it to version control

### 3. Configure Environment Variables

Create or update your `.env` file:

```env
# Firebase Configuration (Choose ONE method)

# Method 1: Path to credentials file (Recommended for development)
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json

# Method 2: JSON string (Recommended for production/deployment)
FIREBASE_CREDENTIALS_JSON='{"type":"service_account","project_id":"your-project",...}'
```

**Security Best Practices:**
- Add `firebase-credentials.json` to `.gitignore`
- Use environment variables for production
- Never hardcode credentials in code

### 4. Database Migration

Run database migrations to create the new tables:

```bash
# Initialize migrations (if not already done)
flask db init

# Create migration for emergency alert tables
flask db migrate -m "Add emergency alert tables"

# Apply migration
flask db upgrade
```

This creates two tables:
- `device_pairings` - Stores device pairing relationships
- `emergency_alerts` - Logs all emergency alerts sent

## 📡 API Endpoints

All endpoints are prefixed with `/api/v1/emergency/`

### 1. Generate Pairing Code

**Endpoint:** `POST /api/v1/emergency/generateCode`

**Request:**
```json
{
  "deviceToken": "firebase_device_token_here",
  "deviceName": "Mom's Phone"
}
```

**Response:**
```json
{
  "success": true,
  "code": "482911",
  "expiresAt": 1700000000000,
  "message": "Pairing code generated successfully"
}
```

**Rate Limit:** 10 requests per hour

---

### 2. Pair Devices

**Endpoint:** `POST /api/v1/emergency/pairDevice`

**Request:**
```json
{
  "code": "482911",
  "deviceToken": "firebase_device_token_b",
  "deviceName": "Dad's Phone"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Devices paired successfully",
  "pairing": {
    "code": "482911",
    "deviceAName": "Mom's Phone",
    "deviceBName": "Dad's Phone",
    "pairedAt": 1700000000000
  }
}
```

**Rate Limit:** 20 requests per hour

---

### 3. Send Emergency Alert

**Endpoint:** `POST /api/v1/emergency/sendEmergency`

**Request:**
```json
{
  "fromDeviceToken": "token_a",
  "reason": "FALL_DETECTED",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "accuracy": 12.5,
  "batteryLevel": 45,
  "timestamp": 1700000000000,
  "message": "Fall detected! User may need help."
}
```

**Supported Reasons:**
- `FALL_DETECTED` - Fall detection triggered
- `SOS_BUTTON` - SOS button pressed
- `PANIC_BUTTON` - Panic button activated
- `EMERGENCY` - General emergency

**Response:**
```json
{
  "success": true,
  "message": "Alert sent to 2 device(s)",
  "alertIds": ["alert_123", "alert_456"],
  "sentCount": 2,
  "totalPaired": 2
}
```

**Rate Limit:** 100 requests per hour

---

### 4. Get Active Pairings

**Endpoint:** `GET /api/v1/emergency/pairings?deviceToken={token}`

**Response:**
```json
{
  "success": true,
  "pairings": [
    {
      "code": "482911",
      "pairedDeviceName": "Dad's Phone",
      "pairedAt": 1700000000000,
      "isActive": true
    }
  ]
}
```

**Rate Limit:** 100 requests per hour

---

### 5. Unpair Devices

**Endpoint:** `DELETE /api/v1/emergency/unpair`

**Request:**
```json
{
  "code": "482911",
  "deviceToken": "token_a"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Devices unpaired successfully"
}
```

**Rate Limit:** 20 requests per hour

---

### 6. Get Alert History

**Endpoint:** `GET /api/v1/emergency/alerts/history?deviceToken={token}&limit=50`

**Query Parameters:**
- `deviceToken` (required) - Device FCM token
- `limit` (optional) - Number of alerts to return (default: 50)

**Response:**
```json
{
  "success": true,
  "alerts": [
    {
      "id": 123,
      "from_device_token": "token_a",
      "to_device_token": "token_b",
      "reason": "FALL_DETECTED",
      "latitude": 28.6139,
      "longitude": 77.2090,
      "accuracy": 12.5,
      "battery_level": 45,
      "message": "Fall detected!",
      "timestamp": 1700000000000,
      "delivered": true,
      "delivered_at": "2024-11-20T10:30:00",
      "created_at": "2024-11-20T10:30:00"
    }
  ]
}
```

**Rate Limit:** 100 requests per hour

## 🧪 Testing

### Using Postman

1. **Import Collection:**
   - Create a new collection named "Emergency Alert System"
   - Add the endpoints listed above

2. **Set Base URL:**
   ```
   http://localhost:5000/api/v1
   ```
   or your production URL

3. **Test Flow:**

   **Step 1: Generate Code (Device A)**
   ```bash
   POST http://localhost:5000/api/v1/emergency/generateCode
   Content-Type: application/json

   {
     "deviceToken": "test_token_a",
     "deviceName": "Test Device A"
   }
   ```

   **Step 2: Pair Device (Device B)**
   ```bash
   POST http://localhost:5000/api/v1/emergency/pairDevice
   Content-Type: application/json

   {
     "code": "482911",
     "deviceToken": "test_token_b",
     "deviceName": "Test Device B"
   }
   ```

   **Step 3: Send Emergency**
   ```bash
   POST http://localhost:5000/api/v1/emergency/sendEmergency
   Content-Type: application/json

   {
     "fromDeviceToken": "test_token_a",
     "reason": "FALL_DETECTED",
     "latitude": 28.6139,
     "longitude": 77.2090,
     "accuracy": 12.5,
     "batteryLevel": 45,
     "timestamp": 1700000000000,
     "message": "Test emergency"
   }
   ```

### Using cURL

```bash
# Generate pairing code
curl -X POST http://localhost:5000/api/v1/emergency/generateCode \
  -H "Content-Type: application/json" \
  -d '{"deviceToken":"test_token_a","deviceName":"Test Device A"}'

# Pair device
curl -X POST http://localhost:5000/api/v1/emergency/pairDevice \
  -H "Content-Type: application/json" \
  -d '{"code":"482911","deviceToken":"test_token_b","deviceName":"Test Device B"}'

# Send emergency
curl -X POST http://localhost:5000/api/v1/emergency/sendEmergency \
  -H "Content-Type: application/json" \
  -d '{"fromDeviceToken":"test_token_a","reason":"FALL_DETECTED","latitude":28.6139,"longitude":77.2090,"accuracy":12.5,"batteryLevel":45,"timestamp":1700000000000,"message":"Test emergency"}'
```

## 🔐 Security Considerations

1. **Firebase Credentials:**
   - Never commit credentials to version control
   - Use environment variables in production
   - Rotate credentials periodically

2. **Rate Limiting:**
   - All endpoints have rate limits to prevent abuse
   - Adjust limits in `api.py` as needed

3. **Device Token Validation:**
   - Validate FCM tokens before pairing
   - Implement token refresh mechanism in mobile app

4. **Data Privacy:**
   - Emergency alerts contain sensitive location data
   - Implement data retention policies
   - Consider encryption for stored alerts

## 📱 Mobile App Integration

### Flutter Example

```dart
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class EmergencyAlertService {
  final String baseUrl = 'https://your-api.com/api/v1/emergency';
  
  // Get FCM token
  Future<String?> getFCMToken() async {
    return await FirebaseMessaging.instance.getToken();
  }
  
  // Generate pairing code
  Future<Map<String, dynamic>> generateCode(String deviceName) async {
    final token = await getFCMToken();
    final response = await http.post(
      Uri.parse('$baseUrl/generateCode'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'deviceToken': token,
        'deviceName': deviceName,
      }),
    );
    return jsonDecode(response.body);
  }
  
  // Pair device
  Future<Map<String, dynamic>> pairDevice(String code, String deviceName) async {
    final token = await getFCMToken();
    final response = await http.post(
      Uri.parse('$baseUrl/pairDevice'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'code': code,
        'deviceToken': token,
        'deviceName': deviceName,
      }),
    );
    return jsonDecode(response.body);
  }
  
  // Send emergency alert
  Future<Map<String, dynamic>> sendEmergency({
    required String reason,
    required double latitude,
    required double longitude,
    double? accuracy,
    int? batteryLevel,
    String? message,
  }) async {
    final token = await getFCMToken();
    final response = await http.post(
      Uri.parse('$baseUrl/sendEmergency'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'fromDeviceToken': token,
        'reason': reason,
        'latitude': latitude,
        'longitude': longitude,
        'accuracy': accuracy,
        'batteryLevel': batteryLevel,
        'timestamp': DateTime.now().millisecondsSinceEpoch,
        'message': message,
      }),
    );
    return jsonDecode(response.body);
  }
}
```

### Handle Incoming Alerts

```dart
// Configure FCM message handler
FirebaseMessaging.onMessage.listen((RemoteMessage message) {
  if (message.data['type'] == 'emergency_alert') {
    // Show emergency screen
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => EmergencyAlertScreen(
          reason: message.data['reason'],
          latitude: double.parse(message.data['latitude']),
          longitude: double.parse(message.data['longitude']),
          deviceName: message.data['deviceName'],
          message: message.data['message'],
        ),
      ),
    );
  }
});
```

## 🐛 Troubleshooting

### Firebase Not Initialized

**Error:** `Firebase credentials not found`

**Solution:**
1. Verify `.env` file contains Firebase credentials
2. Check file path is correct
3. Ensure JSON is properly formatted

### FCM Notification Not Received

**Possible Causes:**
1. Invalid device token
2. Firebase project misconfigured
3. Device not connected to internet
4. App not registered for FCM

**Debug Steps:**
1. Check server logs for FCM errors
2. Verify device token is valid
3. Test with Firebase Console test message
4. Check Android notification channel settings

### Database Errors

**Error:** `Table device_pairings does not exist`

**Solution:**
```bash
flask db upgrade
```

## 📊 Monitoring

### Check System Health

```python
# Check active pairings
SELECT COUNT(*) FROM device_pairings WHERE is_active = 1;

# Check recent alerts
SELECT * FROM emergency_alerts 
ORDER BY created_at DESC 
LIMIT 10;

# Check delivery rate
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN delivered = 1 THEN 1 ELSE 0 END) as delivered,
  (SUM(CASE WHEN delivered = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as delivery_rate
FROM emergency_alerts
WHERE created_at > datetime('now', '-7 days');
```

## 📝 Database Schema

### device_pairings
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| pairing_code | VARCHAR(6) | Unique 6-digit code |
| device_a_token | VARCHAR(255) | FCM token for device A |
| device_b_token | VARCHAR(255) | FCM token for device B |
| device_a_name | VARCHAR(100) | Name of device A |
| device_b_name | VARCHAR(100) | Name of device B |
| created_at | DATETIME | When code was generated |
| expires_at | DATETIME | When code expires (24h) |
| is_active | BOOLEAN | Whether pairing is active |
| paired_at | DATETIME | When devices were paired |

### emergency_alerts
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| from_device_token | VARCHAR(255) | Sender's FCM token |
| to_device_token | VARCHAR(255) | Receiver's FCM token |
| reason | VARCHAR(50) | Alert reason/type |
| latitude | DECIMAL(10,8) | Location latitude |
| longitude | DECIMAL(11,8) | Location longitude |
| accuracy | FLOAT | Location accuracy (meters) |
| battery_level | INTEGER | Battery percentage |
| message | TEXT | Custom message |
| timestamp | BIGINT | Alert timestamp (ms) |
| delivered | BOOLEAN | Whether FCM sent successfully |
| delivered_at | DATETIME | When FCM was delivered |
| created_at | DATETIME | When alert was created |

## 🚀 Deployment

### Production Checklist

- [ ] Firebase credentials configured via environment variables
- [ ] Database migrations applied
- [ ] Rate limits configured appropriately
- [ ] HTTPS enabled for all endpoints
- [ ] CORS configured for mobile app domains
- [ ] Monitoring and logging enabled
- [ ] Backup strategy for database
- [ ] Data retention policy implemented

### Environment Variables

```env
# Production
FIREBASE_CREDENTIALS_JSON='{"type":"service_account",...}'
FLASK_ENV=production
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
```

## 📞 Support

For issues or questions:
1. Check server logs: `logs/fuetime.log`
2. Review Firebase Console for FCM errors
3. Test with Postman collection
4. Check database for pairing/alert records

---

**Version:** 1.0.0  
**Last Updated:** November 2024  
**Author:** Fuetime Development Team
