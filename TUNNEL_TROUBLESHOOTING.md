# #Tunnel Troubleshooting Guide

## #Problem: localhost.run Not Working

### #Symptoms:
```
ssh -R 80:localhost:8000 nokey@localhost.run
ssh: connect to host localhost.run port 22: Connection timed out
```

### #Root Cause Analysis:
- **Port 22 blocked** by ISP or firewall
- **localhost.run down** or overloaded
- **Network restrictions** on SSH connections
- **DNS resolution issues**

---

## #Solutions (in order of preference)

### #1. ngrok (Most Reliable)

**Installation:**
```bash
# Windows
powershell -Command "Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip' -OutFile 'ngrok.zip'"
powershell -Command "Expand-Archive -Path 'ngrok.zip' -DestinationPath '.'"
powershell -Command "Remove-Item 'ngrok.zip'"

# Or download from: https://ngrok.com/download
```

**Usage:**
```bash
ngrok http 8000
```

**Pros:**
- Most reliable
- Free tier available
- HTTPS automatically
- Web interface at http://127.0.0.1:4040

**Cons:**
- Requires registration for free tier
- Limited bandwidth

---

### #2. Cloudflare Tunnel

**Installation:**
```bash
# Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
```

**Usage:**
```bash
cloudflared tunnel --url http://localhost:8000
```

**Pros:**
- Free and unlimited
- Very reliable
- HTTPS automatically
- No registration required

**Cons:**
- Requires installation
- More complex setup

---

### #3. Localtunnel

**Installation:**
```bash
npm install -g localtunnel
```

**Usage:**
```bash
lt --port 8000
```

**Pros:**
- Easy to use
- No registration
- HTTPS automatically

**Cons:**
- Requires Node.js
- Less reliable than ngrok

---

### #4. Serveo

**Usage:**
```bash
ssh -R 80:localhost:8000 serveo.net
```

**Pros:**
- No installation required
- HTTPS automatically
- Custom subdomains available

**Cons:**
- SSH-based (same issue as localhost.run)
- Less reliable

---

## #Quick Fix Script

**Use the automated tunnel manager:**
```bash
python tunnel_alternatives.py
```

This will:
1. Test all tunnel services
2. Auto-select the best working one
3. Provide the public URL

---

## #Network Troubleshooting

### #Check SSH Port Access:
```bash
# Test if port 22 is blocked
Test-NetConnection -ComputerName localhost.run -Port 22

# Test alternative SSH ports
Test-NetConnection -ComputerName github.com -Port 22
Test-NetConnection -ComputerName serveo.net -Port 22
```

### #Check DNS Resolution:
```bash
nslookup localhost.run
nslookup serveo.net
```

### #Check Internet Connection:
```bash
ping google.com
ping 8.8.8.8
```

---

## #Firewall Solutions

### #Windows Firewall:
```powershell
# Allow SSH outbound
New-NetFirewallRule -DisplayName "SSH Outbound" -Direction Outbound -Protocol TCP -LocalPort 22 -Action Allow
```

### #Check ISP Restrictions:
- Contact your ISP about SSH restrictions
- Try using mobile hotspot (different network)
- Use VPN service to bypass restrictions

---

## #Alternative Approaches

### #1. Direct IP Access
If you have public IP:
```bash
# Make server public
python manage.py runserver 0.0.0.0:8000

# Access via: http://YOUR_PUBLIC_IP:8000
```

### #2. Port Forwarding
Configure your router:
- Forward port 8000 to your machine
- Access via: http://YOUR_PUBLIC_IP:8000

### #3. Cloud Deployment
Deploy to cloud platform:
- Heroku (free tier)
- PythonAnywhere
- DigitalOcean
- AWS EC2 (free tier)

---

## #Testing Tunnel Services

### #Automated Testing:
```bash
python tunnel_alternatives.py
# Choose option 5 to test all services
```

### #Manual Testing:
```bash
# Test ngrok
ngrok http 8000

# Test cloudflared
cloudflared tunnel --url http://localhost:8000

# Test localtunnel
lt --port 8000

# Test serveo
ssh -R 80:localhost:8000 serveo.net
```

---

## #Common Issues and Solutions

### #Issue: "Port already in use"
**Solution:**
```bash
# Find and kill process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
python manage.py runserver 0.0.0.0:8001
```

### #Issue: "Connection refused"
**Solution:**
```bash
# Make sure Django server is running
python manage.py runserver 0.0.0.0:8000

# Check if server responds
curl http://localhost:8000
```

### #Issue: "Authentication required"
**Solution:**
```bash
# For ngrok - configure auth token
ngrok config add-authtoken YOUR_AUTH_TOKEN

# Get token from: https://dashboard.ngrok.com/auth
```

### #Issue: "Rate limited"
**Solution:**
- Wait for rate limit to reset
- Use different tunnel service
- Upgrade to paid plan

---

## #Best Practices

### #1. Use ngrok for development
- Most reliable
- Good documentation
- Active development

### #2. Use Cloudflare Tunnel for production
- Free and unlimited
- Enterprise-grade
- Better performance

### #3. Keep backup options ready
- Install multiple tunnel services
- Test them before important presentations
- Have cloud deployment as fallback

### #4. Monitor tunnel status
```bash
# ngrok web interface
http://127.0.0.1:4040

# Check tunnel logs
tail -f ~/.ngrok/ngrok.log
```

---

## #Emergency Quick Start

**If you need a tunnel NOW:**
```bash
# Option 1: ngrok (fastest)
ngrok http 8000

# Option 2: automated script
python tunnel_alternatives.py
# Choose option 6 for auto-select
```

**Both should work within 30 seconds!**

---

## #Contact Support

If none of the solutions work:
1. Check your internet connection
2. Try from different network
3. Contact your ISP about SSH restrictions
4. Use cloud deployment as fallback

---

*Last updated: April 9, 2026*  
*Tested with: Windows 10, Python 3.9+, Django 4.2+*
