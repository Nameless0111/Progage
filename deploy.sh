#!/bin/bash

# Deployment script for Progage
set -e

echo "🚀 Starting deployment..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx redis-server supervisor

# Create project directory
sudo mkdir -p /var/www/progage
sudo chown $USER:$USER /var/www/progage
cd /var/www/progage

# Clone repository (replace with your repo)
# git clone https://github.com/yourusername/progage.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Setup PostgreSQL
sudo -u postgres createdb progage
sudo -u postgres createuser --interactive
# When prompted, create a user with same name as your Linux user

# Copy environment file
cp .env.example .env
# Edit .env with your actual values
nano .env

# Django setup
export DJANGO_SETTINGS_MODULE=progage.production
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createsuperuser

# Setup Nginx
sudo tee /etc/nginx/sites-available/progage > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    location /static/ {
        alias /var/www/progage/staticfiles/;
        expires 30d;
    }
    
    location /media/ {
        alias /var/www/progage/mediafiles/;
        expires 30d;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # WebSocket support for Django Channels
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/progage /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Setup Supervisor for Gunicorn
sudo tee /etc/supervisor/conf.d/progage.conf > /dev/null <<EOF
[program:progage]
command=/var/www/progage/venv/bin/gunicorn --config gunicorn.conf.py progage.wsgi:application
directory=/var/www/progage
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/gunicorn/progage.log
environment=DJANGO_SETTINGS_MODULE=progage.production
EOF

# Setup Supervisor for Daphne (WebSocket server)
sudo tee /etc/supervisor/conf.d/daphne.conf > /dev/null <<EOF
[program:daphne]
command=/var/www/progage/venv/bin/daphne -b 0.0.0.0 -p 8001 progage.asgi:application
directory=/var/www/progage
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/daphne/progage.log
environment=DJANGO_SETTINGS_MODULE=progage.production
EOF

# Start services
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start progage
sudo supervisorctl start daphne

# Setup SSL with Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Setup log rotation
sudo tee /etc/logrotate.d/progage > /dev/null <<EOF
/var/log/gunicorn/progage.log /var/log/daphne/progage.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        supervisorctl restart progage daphne
    endscript
}
EOF

echo "✅ Deployment complete!"
echo "🌐 Your site should be available at: https://your-domain.com"
echo "📝 Don't forget to:"
echo "   1. Update your-domain.com in all config files"
echo "   2. Set up reCAPTCHA keys in .env"
echo "   3. Configure email settings"
echo "   4. Set up SSL certificate renewal: sudo crontab -e"
echo "      Add: 0 12 * * * /usr/bin/certbot renew --quiet"
