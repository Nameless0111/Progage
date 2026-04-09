#!/usr/bin/env python
"""
Alternative tunneling solutions for Progage
Works when localhost.run is unavailable
"""
import subprocess
import time
import sys
import os
from urllib.parse import urlparse

class TunnelManager:
    def __init__(self, local_port=8000):
        self.local_port = local_port
        self.tunnel_services = {
            'ngrok': self.setup_ngrok,
            'cloudflared': self.setup_cloudflared,
            'localtunnel': self.setup_localtunnel,
            'serveo': self.setup_serveo,
        }
    
    def setup_ngrok(self):
        """Setup ngrok tunnel"""
        print("Setting up ngrok tunnel...")
        try:
            # Check if ngrok is installed
            result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
            if result.returncode != 0:
                print("ngrok not found. Installing...")
                # Download ngrok
                if sys.platform == "win32":
                    subprocess.run(['powershell', '-Command', 
                        'Invoke-WebRequest -Uri "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip" -OutFile "ngrok.zip"'], 
                        check=True)
                    subprocess.run(['powershell', '-Command', 'Expand-Archive -Path "ngrok.zip" -DestinationPath "."'], check=True)
                    subprocess.run(['powershell', '-Command', 'Remove-Item "ngrok.zip"'], check=True)
            
            # Start ngrok
            cmd = ['ngrok', 'http', str(self.local_port), '--log=stdout']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            print("ngrok started. Waiting for tunnel URL...")
            time.sleep(3)
            
            # Try to get the URL from ngrok API
            try:
                import requests
                response = requests.get('http://127.0.0.1:4040/api/tunnels')
                if response.status_code == 200:
                    tunnels = response.json()['tunnels']
                    if tunnels:
                        public_url = tunnels[0]['public_url']
                        print(f"ngrok tunnel URL: {public_url}")
                        return public_url
            except:
                pass
            
            print("ngrok tunnel running. Check http://127.0.0.1:4040 for URL")
            return "http://127.0.0.1:4040"
            
        except Exception as e:
            print(f"ngrok setup failed: {e}")
            return None
    
    def setup_cloudflared(self):
        """Setup Cloudflare tunnel"""
        print("Setting up Cloudflare tunnel...")
        try:
            # Check if cloudflared is installed
            result = subprocess.run(['cloudflared', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                print("cloudflared not found. Please install from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")
                return None
            
            # Start cloudflared
            cmd = ['cloudflared', 'tunnel', '--url', f'http://localhost:{self.local_port}']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            print("Cloudflare tunnel starting...")
            time.sleep(5)
            
            # Parse output for URL
            for line in iter(process.stdout.readline, ''):
                if 'https://' in line and '.trycloudflare.com' in line:
                    url = line.strip()
                    print(f"Cloudflare tunnel URL: {url}")
                    return url
            
            return None
            
        except Exception as e:
            print(f"Cloudflare setup failed: {e}")
            return None
    
    def setup_localtunnel(self):
        """Setup localtunnel"""
        print("Setting up localtunnel...")
        try:
            # Check if localtunnel is installed
            result = subprocess.run(['lt', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                print("Installing localtunnel...")
                subprocess.run(['npm', 'install', '-g', 'localtunnel'], check=True)
            
            # Start localtunnel
            cmd = ['lt', '--port', str(self.local_port)]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            print("Localtunnel starting...")
            time.sleep(3)
            
            # Parse output for URL
            for line in iter(process.stdout.readline, ''):
                if 'https://' in line and '.loca.lt' in line:
                    url = line.strip()
                    print(f"Localtunnel URL: {url}")
                    return url
            
            return None
            
        except Exception as e:
            print(f"Localtunnel setup failed: {e}")
            return None
    
    def setup_serveo(self):
        """Setup Serveo tunnel"""
        print("Setting up Serveo tunnel...")
        try:
            # Start serveo
            cmd = ['ssh', '-R', f'80:localhost:{self.local_port}', 'serveo.net']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            print("Serveo tunnel starting...")
            time.sleep(5)
            
            # Parse output for URL
            for line in iter(process.stdout.readline, ''):
                if 'https://' in line and '.serveo.net' in line:
                    url = line.strip()
                    print(f"Serveo tunnel URL: {url}")
                    return url
            
            return None
            
        except Exception as e:
            print(f"Serveo setup failed: {e}")
            return None
    
    def test_all_tunnels(self):
        """Test all available tunnel services"""
        print("Testing all tunnel services...")
        results = {}
        
        for service_name, setup_func in self.tunnel_services.items():
            print(f"\n{'='*50}")
            print(f"Testing {service_name}")
            print('='*50)
            
            try:
                url = setup_func()
                if url:
                    results[service_name] = url
                    print(f"SUCCESS: {service_name} - {url}")
                else:
                    print(f"FAILED: {service_name}")
            except Exception as e:
                print(f"ERROR: {service_name} - {e}")
        
        return results
    
    def setup_best_tunnel(self):
        """Setup the first working tunnel"""
        print("Setting up best available tunnel...")
        
        for service_name, setup_func in self.tunnel_services.items():
            print(f"\nTrying {service_name}...")
            try:
                url = setup_func()
                if url:
                    print(f"SUCCESS: Using {service_name} - {url}")
                    return url
            except Exception as e:
                print(f"FAILED: {service_name} - {e}")
                continue
        
        print("All tunnel services failed!")
        return None

def main():
    """Main function"""
    print("Tunnel Manager for Progage")
    print("=" * 40)
    
    # Check if local server is running
    try:
        import requests
        response = requests.get(f'http://localhost:8000', timeout=5)
        if response.status_code != 200:
            print("Local server is not responding correctly!")
            print("Please start your Django server first:")
            print("python manage.py runserver 0.0.0.0:8000")
            return
    except:
        print("Local server is not running!")
        print("Please start your Django server first:")
        print("python manage.py runserver 0.0.0.0:8000")
        return
    
    tunnel_manager = TunnelManager()
    
    choice = input("""
Choose tunnel service:
1. ngrok (recommended)
2. Cloudflare
3. Localtunnel
4. Serveo
5. Test all
6. Auto-select best

Choice (1-6): """).strip()
    
    if choice == '1':
        tunnel_manager.setup_ngrok()
    elif choice == '2':
        tunnel_manager.setup_cloudflared()
    elif choice == '3':
        tunnel_manager.setup_localtunnel()
    elif choice == '4':
        tunnel_manager.setup_serveo()
    elif choice == '5':
        results = tunnel_manager.test_all_tunnels()
        print(f"\nResults: {results}")
    elif choice == '6':
        url = tunnel_manager.setup_best_tunnel()
        if url:
            print(f"\nTunnel ready: {url}")
        else:
            print("\nNo working tunnel found!")
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()
