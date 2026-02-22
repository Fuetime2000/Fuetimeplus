# Environment Setup Instructions

## 🔐 Environment Variables Setup

This application uses environment variables to manage sensitive configuration. Follow these steps to set up your development environment:

### 1. Install Required Dependencies

```bash
pip install python-dotenv
```

### 2. Copy Environment Template

```bash
cp .env.example .env
```

### 3. Configure Your Environment Variables

Edit the `.env` file with your actual credentials:

#### 📧 Email Configuration (Amazon SES)
```env
MAIL_SERVER=email-smtp.eu-north-1.amazonaws.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your-ses-smtp-username
MAIL_PASSWORD=your-ses-smtp-password
MAIL_DEFAULT_SENDER=noreply@fuetime.com
```

#### 🔑 Application Configuration
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
SECURITY_PASSWORD_SALT=your-password-salt-here
```

#### 🗄️ Database Configuration
```env
DATABASE_URL=sqlite:///fuetime.db
```

#### 💳 Payment Configuration
```env
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-secret
```

### 4. Security Notes

⚠️ **IMPORTANT**: The `.env` file is already included in `.gitignore` and will NOT be committed to version control.

- Never commit your `.env` file to Git
- Use different credentials for development and production
- Rotate your credentials regularly
- Use strong, unique passwords

### 5. Production Deployment

For production deployment:

1. Set environment variables directly in your hosting environment
2. Do NOT store the `.env` file on production servers
3. Use environment-specific configuration management
4. Enable all security features (HTTPS, CSRF protection, etc.)

### 6. Amazon SES Setup

To use Amazon SES:

1. **Create AWS Account**: Sign up at [AWS Console](https://console.aws.amazon.com)
2. **Verify Domain**: Verify `fuetime.com` in SES console
3. **Create SMTP Credentials**: Generate SMTP credentials in SES → SMTP Settings
4. **Update Configuration**: Add credentials to your `.env` file
5. **Test Sending**: Use the test script to verify email functionality

### 7. Loading Environment Variables

The application automatically loads environment variables from `.env` file using:

```python
from dotenv import load_dotenv
load_dotenv()
```

All configuration is loaded using:
```python
os.environ.get('VARIABLE_NAME', 'default_value')
```

### 8. Troubleshooting

**Email Not Sending:**
- Verify SES credentials are correct
- Check if domain is verified in SES
- Ensure you're out of SES sandbox mode
- Check SMTP server and port settings

**Environment Variables Not Loading:**
- Ensure `.env` file exists in project root
- Install `python-dotenv` package
- Check file permissions

**Git Issues:**
- Verify `.env` is in `.gitignore`
- Use `git status` to check if `.env` is being tracked
- Remove from git history if accidentally committed: `git filter-branch`
