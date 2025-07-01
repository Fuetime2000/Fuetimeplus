#!/bin/bash

echo "🔄 Pulling latest code from GitHub..."
cd /home/ubuntu/Fuetimeplus || exit
git pull origin main

echo "📦 Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "🚀 Restarting Gunicorn service..."
sudo systemctl restart fuetime

echo "✅ Deployment complete! Visit: https://fuetime.com"
