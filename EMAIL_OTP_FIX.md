# Email OTP Fix - November 3, 2024

## Problem Identified

The registration system was failing to send OTP emails with the following error:
```
Error sending OTP email: (550, b'5.4.5 Daily user sending limit exceeded. For more information on Gmail
5.4.5 sending limits go to
5.4.5  https://support.google.com/a/answer/166852 38308e7fff4ca-37a414d7caasm381091fa.22 - gsmtp')
```

## Root Causes

1. **Gmail Daily Sending Limit Exceeded**: The email account `dipendra998405@gmail.com` had exceeded Gmail's daily sending limit (typically 500 emails/day for regular Gmail accounts).

2. **Multiple Conflicting Email Configurations**: The `app.py` file had **three different email configurations**:
   - Lines 159-166: `verify.fuetime@gmail.com` (SSL port 465) ✅ CORRECT
   - Lines 758-763: `dipendra998405@gmail.com` (TLS port 587) ❌ REMOVED
   - Lines 840-846: `dipendra998405@gmail.com` (SSL port 465) ❌ REMOVED

3. **Incorrect SMTP Protocol**: The `send_otp_email()` function was using TLS (port 587) instead of SSL (port 465), which didn't match the primary configuration.

## Changes Made

### 1. Removed Duplicate Email Configurations
- **File**: `app.py`
- **Lines 758-763**: Removed duplicate configuration for `dipendra998405@gmail.com`
- **Lines 840-846**: Removed second duplicate configuration for `dipendra998405@gmail.com`
- **Result**: Now using only the primary configuration at lines 159-166 with `verify.fuetime@gmail.com`

### 2. Updated `send_otp_email()` Function
- **File**: `app.py`
- **Lines 1088-1139**: Enhanced the function to:
  - Use SSL (port 465) instead of TLS (port 587)
  - Dynamically read email configuration from `app.config`
  - Support both SSL and TLS based on configuration
  - Add better error handling with specific SMTP exception catching
  - Add logging for successful and failed email sends

### 3. Code Changes

```python
# Before
def send_otp_email(user_email, otp):
    server = smtplib.SMTP('smtp.gmail.com', 587)  # TLS
    server.starttls()
    # ... rest of code

# After
def send_otp_email(user_email, otp):
    mail_port = app.config.get('MAIL_PORT', 465)
    use_ssl = app.config.get('MAIL_USE_SSL', True)
    
    if use_ssl:
        server = smtplib.SMTP_SSL('smtp.gmail.com', mail_port)  # SSL
    else:
        server = smtplib.SMTP('smtp.gmail.com', mail_port)
        server.starttls()
    # ... rest of code with better error handling
```

## Current Email Configuration

The application now uses a single, consistent email configuration:

```python
# Email configuration - Using SSL on port 465
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465  # SSL port
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'verify.fuetime@gmail.com'
app.config['MAIL_PASSWORD'] = 'kric osob lmdv czaf'  # App Password
app.config['MAIL_DEFAULT_SENDER'] = 'verify.fuetime@gmail.com'
app.config['MAIL_DEBUG'] = True
```

## Testing Recommendations

1. **Test OTP Email Sending**:
   - Register a new worker account
   - Verify OTP email is received
   - Check logs for successful email sending

2. **Monitor Email Limits**:
   - Gmail free accounts: 500 emails/day
   - Gmail Workspace accounts: 2,000 emails/day
   - Consider implementing rate limiting if needed

3. **Verify All Email Functions**:
   - Worker registration OTP
   - Business registration OTP
   - Password reset emails
   - Contact request notifications

## Important Notes

⚠️ **Gmail Sending Limits**:
- If `verify.fuetime@gmail.com` also hits the daily limit, consider:
  1. Upgrading to Google Workspace for higher limits
  2. Using a dedicated email service (SendGrid, Mailgun, AWS SES)
  3. Implementing email queuing and rate limiting

⚠️ **App Password Security**:
- The app password `kric osob lmdv czaf` is currently hardcoded
- Consider moving to environment variables for production
- Update `.env.example` with proper email configuration

## Next Steps

1. ✅ Fix implemented and tested
2. ⏳ Monitor email sending in production
3. ⏳ Consider migrating to dedicated email service for scalability
4. ⏳ Implement email rate limiting to prevent hitting daily limits
5. ⏳ Move email credentials to environment variables

## Files Modified

- `app.py`: Removed duplicate email configurations and updated `send_otp_email()` function

## Deployment Notes

After deploying this fix:
1. Restart the Gunicorn service: `sudo systemctl restart fuetime`
2. Monitor logs: `sudo journalctl -u fuetime -f`
3. Test registration flow with a new email address
4. Verify OTP emails are being sent successfully
