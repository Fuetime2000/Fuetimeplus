#!/bin/bash

# Exit if any command fails
set -e

echo "🔧 Starting Fuetime Deployment on AWS EC2..."

# Update and install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx git -y

# Clone the Fuetime project
cd /home/ubuntu
rm -rf Fuetimeplus || true
git clone https://github.com/Fuetime2000/Fuetimeplus.git
cd Fuetimeplus

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required Python packages
pip install --upgrade pip
pip install -r requirements.txt

# Install gevent for better compatibility
pip install gevent

echo "⚙️ Creating Gunicorn systemd service..."

# Create Gunicorn service file with gevent worker
sudo tee /etc/systemd/system/fuetime.service > /dev/null <<EOF
[Unit]
Description=Fuetime Flask SocketIO App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Fuetimeplus
Environment="PATH=/home/ubuntu/Fuetimeplus/venv/bin"
ExecStart=/home/ubuntu/Fuetimeplus/venv/bin/gunicorn --worker-class gevent --worker-connections 1000 -w 1 --timeout 120 --graceful-timeout 120 --log-level=debug app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable fuetime
sudo systemctl start fuetime

echo "🚀 Gunicorn service is running!"

# Configure NGINX
echo "🌐 Setting up NGINX..."

sudo tee /etc/nginx/sites-available/fuetime > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
EOF

# Enable NGINX site and restart
sudo ln -sf /etc/nginx/sites-available/fuetime /etc/nginx/sites-enabled/fuetime
sudo nginx -t && sudo systemctl restart nginx

echo "✅ Deployment complete! Your Fuetime app is now live."

# Print public IP
echo "🌍 Your application should be available at:"
curl -s http://checkip.amazonaws.com
