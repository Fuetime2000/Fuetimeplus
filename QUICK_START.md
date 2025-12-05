# Emergency Alert System - Quick Start Guide

Get the Emergency Alert System up and running in 5 minutes!

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Dependencies (1 min)
```bash
pip install -r requirements.txt
```

### Step 2: Setup Database (1 min)
```bash
# Create migration
flask db migrate -m "Add emergency alert tables"

# Apply migration
flask db upgrade
```

### Step 3: Configure Firebase (2 mins)

**Option A: Skip Firebase for Testing**
- The system will work without Firebase
- Alerts will be logged but not sent via FCM
- Perfect for API testing

**Option B: Quick Firebase Setup**
1. Download Firebase credentials JSON from Firebase Console
2. Add to `.env`:
   ```env
   FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
   ```

### Step 4: Test the API (1 min)

**Import Postman Collection:**
```bash
# Import postman_collection.json into Postman
# Or use cURL commands below
```

**Test with cURL:**
```bash
# 1. Generate code
curl -X POST http://localhost:5000/api/v1/emergency/generateCode \
  -H "Content-Type: application/json" \
  -d '{"deviceToken":"test_a","deviceName":"Device A"}'

# Copy the code from response (e.g., "482911")

# 2. Pair device
curl -X POST http://localhost:5000/api/v1/emergency/pairDevice \
  -H "Content-Type: application/json" \
  -d '{"code":"482911","deviceToken":"test_b","deviceName":"Device B"}'

# 3. Send emergency
curl -X POST http://localhost:5000/api/v1/emergency/sendEmergency \
  -H "Content-Type: application/json" \
  -d '{"fromDeviceToken":"test_a","reason":"FALL_DETECTED","latitude":28.6139,"longitude":77.2090,"batteryLevel":45,"timestamp":1700000000000}'
```

## ✅ Verification

Check if everything works:

```bash
# Check database tables exist
sqlite3 fuetime.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%emergency%';"

# Should show:
# device_pairings
# emergency_alerts

# Check active pairings
curl "http://localhost:5000/api/v1/emergency/pairings?deviceToken=test_a"

# Check alert history
curl "http://localhost:5000/api/v1/emergency/alerts/history?deviceToken=test_a"
```

## 📱 Mobile App Integration

### Flutter Quick Start

1. **Add Firebase to your Flutter app:**
   ```yaml
   # pubspec.yaml
   dependencies:
     firebase_core: ^2.24.0
     firebase_messaging: ^14.7.0
     http: ^1.1.0
   ```

2. **Get FCM Token:**
   ```dart
   final token = await FirebaseMessaging.instance.getToken();
   print('FCM Token: $token');
   ```

3. **Use the token in API calls:**
   ```dart
   // Replace 'test_a' with actual FCM token
   final response = await http.post(
     Uri.parse('http://your-server.com/api/v1/emergency/generateCode'),
     headers: {'Content-Type': 'application/json'},
     body: jsonEncode({
       'deviceToken': token,
       'deviceName': 'My Phone',
     }),
   );
   ```

4. **Handle incoming alerts:**
   ```dart
   FirebaseMessaging.onMessage.listen((RemoteMessage message) {
     if (message.data['type'] == 'emergency_alert') {
       // Show emergency screen
       showEmergencyAlert(message.data);
     }
   });
   ```

## 🎯 Common Use Cases

### Use Case 1: Fall Detection
```bash
curl -X POST http://localhost:5000/api/v1/emergency/sendEmergency \
  -H "Content-Type: application/json" \
  -d '{
    "fromDeviceToken": "elderly_device_token",
    "reason": "FALL_DETECTED",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "accuracy": 12.5,
    "batteryLevel": 45,
    "timestamp": 1700000000000,
    "message": "Fall detected! User may need help."
  }'
```

### Use Case 2: SOS Button
```bash
curl -X POST http://localhost:5000/api/v1/emergency/sendEmergency \
  -H "Content-Type: application/json" \
  -d '{
    "fromDeviceToken": "user_device_token",
    "reason": "SOS_BUTTON",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "batteryLevel": 30,
    "timestamp": 1700000000000,
    "message": "SOS! Need immediate help!"
  }'
```

### Use Case 3: Multiple Paired Devices
```bash
# Device A pairs with Device B
curl -X POST http://localhost:5000/api/v1/emergency/generateCode \
  -d '{"deviceToken":"device_a","deviceName":"Mom"}'
# Get code: 123456

curl -X POST http://localhost:5000/api/v1/emergency/pairDevice \
  -d '{"code":"123456","deviceToken":"device_b","deviceName":"Dad"}'

# Device A pairs with Device C
curl -X POST http://localhost:5000/api/v1/emergency/generateCode \
  -d '{"deviceToken":"device_a","deviceName":"Mom"}'
# Get code: 789012

curl -X POST http://localhost:5000/api/v1/emergency/pairDevice \
  -d '{"code":"789012","deviceToken":"device_c","deviceName":"Sister"}'

# Now when Device A sends emergency, both B and C receive it
curl -X POST http://localhost:5000/api/v1/emergency/sendEmergency \
  -d '{"fromDeviceToken":"device_a","reason":"EMERGENCY",...}'
```

## 🔧 Troubleshooting

### Problem: "Table does not exist"
**Solution:**
```bash
flask db upgrade
```

### Problem: "Firebase not initialized"
**Solution:**
- For testing: Ignore this warning, API will still work
- For production: Add Firebase credentials to `.env`

### Problem: "Rate limit exceeded"
**Solution:**
- Wait for rate limit to reset (1 hour)
- Or adjust limits in `blueprints/api.py`

### Problem: "Pairing code expired"
**Solution:**
- Codes expire after 24 hours
- Generate a new code

## 📚 Next Steps

1. **Read Full Documentation:**
   - `EMERGENCY_ALERT_SETUP.md` - Complete setup guide
   - `docs/EMERGENCY_ALERT_API.md` - API reference

2. **Configure Firebase:**
   - Set up Firebase project
   - Add credentials for FCM notifications

3. **Integrate with Mobile App:**
   - Implement pairing UI
   - Handle emergency notifications
   - Test end-to-end flow

4. **Deploy to Production:**
   - Set up environment variables
   - Enable HTTPS
   - Configure monitoring

## 🎉 You're Ready!

The Emergency Alert System is now set up and ready to use. Start testing with the Postman collection or integrate with your mobile app.

**Need Help?**
- Check `EMERGENCY_ALERT_SETUP.md` for detailed setup
- Review `docs/EMERGENCY_ALERT_API.md` for API details
- Check logs at `logs/fuetime.log`

---

**Quick Links:**
- [Complete Setup Guide](EMERGENCY_ALERT_SETUP.md)
- [API Documentation](docs/EMERGENCY_ALERT_API.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
