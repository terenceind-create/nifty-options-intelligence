# desktop_app.py
import webview
import subprocess
import time
import sys
import socket
from src.data.upstox_auth import UpstoxAuth

def is_port_open(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def check_token():
    """Check if Upstox token is valid before starting"""
    print("Checking Upstox token...")
    auth = UpstoxAuth()
    
    if auth.is_token_valid():
        print("✅ Token valid!")
        return True
    
    print("⚠️ Token expired! Running authentication...")
    
    auth_url = auth.get_auth_url()
    print(f"\n1. Open this URL in your browser:\n\n{auth_url}\n")
    print("2. Log in and authorize")
    print("3. Copy the FULL redirect URL from your browser\n")
    
    redirect_url = input("Paste redirect URL: ").strip()
    
    if 'code=' in redirect_url:
        auth_code = redirect_url.split('code=')[1].split('&')[0]
        token = auth.generate_token_from_code(auth_code)
        if token:
            print("✅ Token renewed!")
            return True
        else:
            print("❌ Failed to renew token")
            return False
    else:
        print("❌ No code found in URL")
        return False

def start_collector():
    subprocess.Popen(
        [sys.executable, "run_collector.py"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    )

def start_streamlit():
    subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "src/dashboard/app.py",
         "--server.headless", "true", "--server.port", "8501",
         "--browser.gatherUsageStats", "false"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    )

def main():
    print("=" * 60)
    print("  🎯 OPTION BUYER INTELLIGENCE - DESKTOP APP")
    print("=" * 60)
    
    # Check token FIRST
    if not check_token():
        print("\n❌ Cannot start without valid token")
        input("Press Enter to exit...")
        return
    
    if not is_port_open(8501):
        print("\n[1/2] Starting data collector...")
        start_collector()
        time.sleep(2)
        
        print("[2/2] Starting dashboard server...")
        start_streamlit()
        time.sleep(6)
    else:
        print("\n✅ Dashboard already running")
    
    print("Opening desktop window...")
    
    window = webview.create_window(
        title="🎯 Option Buyer Intelligence",
        url="http://localhost:8501",
        width=1440, height=900,
        resizable=True, min_size=(1100, 700)
    )
    
    webview.start()

if __name__ == "__main__":
    main()