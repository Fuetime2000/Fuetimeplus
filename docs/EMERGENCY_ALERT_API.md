# Emergency Alert System - API Quick Reference

## Base URL
```
Production: https://your-domain.com/api/v1/emergency
Development: http://localhost:5000/api/v1/emergency
```

## Authentication
No authentication required for emergency endpoints (by design for emergency situations).

## Endpoints Summary

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/generateCode` | Generate pairing code | 10/hour |
| POST | `/pairDevice` | Pair two devices | 20/hour |
| POST | `/sendEmergency` | Send emergency alert | 100/hour |
| GET | `/pairings` | Get active pairings | 100/hour |
| DELETE | `/unpair` | Unpair devices | 20/hour |
| GET | `/alerts/history` | Get alert history | 100/hour |

---

## 1. Generate Pairing Code

Create a 6-digit code for device pairing.

**Endpoint:** `POST /generateCode`

**Request:**
```json
{
  "deviceToken": "fcm_token_here",
  "deviceName": "Mom's Phone"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "code": "482911",
  "expiresAt": 1700000000000,
  "message": "Pairing code generated successfully"
}
```

**Error Response (400):**
```json
{
  "success": false,
  "message": "Device token is required"
}
```

---

## 2. Pair Device

Pair a device using a pairing code.

**Endpoint:** `POST /pairDevice`

**Request:**
```json
{
  "code": "482911",
  "deviceToken": "fcm_token_b",
  "deviceName": "Dad's Phone"
}
```

**Success Response (200):**
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

**Error Responses:**

**404 - Invalid Code:**
```json
{
  "success": false,
  "message": "Invalid pairing code"
}
```

**400 - Code Expired:**
```json
{
  "success": false,
  "message": "Pairing code has expired"
}
```

**400 - Already Used:**
```json
{
  "success": false,
  "message": "This code has already been used"
}
```

---

## 3. Send Emergency Alert

Send emergency alert to all paired devices.

**Endpoint:** `POST /sendEmergency`

**Request:**
```json
{
  "fromDeviceToken": "fcm_token_a",
  "reason": "FALL_DETECTED",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "accuracy": 12.5,
  "batteryLevel": 45,
  "timestamp": 1700000000000,
  "message": "Fall detected! User may need help."
}
```

**Alert Reasons:**
- `FALL_DETECTED` - Fall detection sensor triggered
- `SOS_BUTTON` - SOS button pressed
- `PANIC_BUTTON` - Panic button activated
- `EMERGENCY` - General emergency

**Success Response (200):**
```json
{
  "success": true,
  "message": "Alert sent to 2 device(s)",
  "alertIds": ["alert_123", "alert_456"],
  "sentCount": 2,
  "totalPaired": 2
}
```

**Error Response (404):**
```json
{
  "success": false,
  "message": "No paired devices found"
}
```

---

## 4. Get Active Pairings

Retrieve all active pairings for a device.

**Endpoint:** `GET /pairings?deviceToken={token}`

**Query Parameters:**
- `deviceToken` (required) - FCM device token

**Success Response (200):**
```json
{
  "success": true,
  "pairings": [
    {
      "code": "482911",
      "pairedDeviceName": "Dad's Phone",
      "pairedAt": 1700000000000,
      "isActive": true
    },
    {
      "code": "123456",
      "pairedDeviceName": "Sister's Phone",
      "pairedAt": 1699999999000,
      "isActive": true
    }
  ]
}
```

---

## 5. Unpair Devices

Deactivate a device pairing.

**Endpoint:** `DELETE /unpair`

**Request:**
```json
{
  "code": "482911",
  "deviceToken": "fcm_token_a"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Devices unpaired successfully"
}
```

**Error Responses:**

**404 - Not Found:**
```json
{
  "success": false,
  "message": "Pairing not found"
}
```

**403 - Unauthorized:**
```json
{
  "success": false,
  "message": "Unauthorized to unpair these devices"
}
```

---

## 6. Get Alert History

Retrieve emergency alert history for a device.

**Endpoint:** `GET /alerts/history?deviceToken={token}&limit=50`

**Query Parameters:**
- `deviceToken` (required) - FCM device token
- `limit` (optional) - Number of alerts (default: 50, max: 100)

**Success Response (200):**
```json
{
  "success": true,
  "alerts": [
    {
      "id": 123,
      "from_device_token": "fcm_token_a",
      "to_device_token": "fcm_token_b",
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

---

## Error Codes

| HTTP Code | Meaning |
|-----------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 403 | Forbidden - Unauthorized action |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## Rate Limiting

All endpoints are rate-limited to prevent abuse:

| Endpoint | Limit |
|----------|-------|
| Generate Code | 10 requests/hour |
| Pair Device | 20 requests/hour |
| Send Emergency | 100 requests/hour |
| Get Pairings | 100 requests/hour |
| Unpair | 20 requests/hour |
| Alert History | 100 requests/hour |

**Rate Limit Response (429):**
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later."
}
```

---

## Example Workflow

### Complete Pairing Flow

```bash
# Step 1: Device A generates code
curl -X POST http://localhost:5000/api/v1/emergency/generateCode \
  -H "Content-Type: application/json" \
  -d '{
    "deviceToken": "device_a_fcm_token",
    "deviceName": "Mom'\''s Phone"
  }'

# Response: {"success":true,"code":"482911",...}

# Step 2: Device B pairs using code
curl -X POST http://localhost:5000/api/v1/emergency/pairDevice \
  -H "Content-Type: application/json" \
  -d '{
    "code": "482911",
    "deviceToken": "device_b_fcm_token",
    "deviceName": "Dad'\''s Phone"
  }'

# Response: {"success":true,"message":"Devices paired successfully",...}

# Step 3: Device A sends emergency
curl -X POST http://localhost:5000/api/v1/emergency/sendEmergency \
  -H "Content-Type: application/json" \
  -d '{
    "fromDeviceToken": "device_a_fcm_token",
    "reason": "FALL_DETECTED",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "accuracy": 12.5,
    "batteryLevel": 45,
    "timestamp": 1700000000000,
    "message": "Fall detected!"
  }'

# Response: {"success":true,"message":"Alert sent to 1 device(s)",...}
```

---

## Testing Tips

1. **Use Test Tokens:** For development, use dummy FCM tokens like `test_token_a`, `test_token_b`
2. **Check Logs:** Monitor `logs/fuetime.log` for detailed error messages
3. **Verify Pairing:** Use `/pairings` endpoint to confirm pairing status
4. **Test Expiration:** Codes expire after 24 hours
5. **Multiple Pairings:** A device can be paired with multiple devices

---

## Security Notes

- No authentication required (emergency use case)
- Rate limiting prevents abuse
- Pairing codes expire in 24 hours
- Device tokens should be kept secure
- Location data is sensitive - handle appropriately

---

## Support

For issues or questions:
- Check `EMERGENCY_ALERT_SETUP.md` for detailed setup
- Review server logs at `logs/fuetime.log`
- Test with Postman collection
- Verify Firebase configuration

**Last Updated:** November 2024
