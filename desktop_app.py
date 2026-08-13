# desktop_app.py
import webview
import threading
import subprocess
import time
import sys
import os
import socket

def is_port_open(port):
    """Check if a port is already in use"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def start_collector():
    """Start data collector in background"""
    if sys.platform == 'win32':
        subprocess.Popen(
            [sys.executable, "run_collector.py"],
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    else:
        subprocess.Popen(
            [sys.executable, "run_collector.py"],
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )

def start_streamlit():
    """Start Streamlit server in background"""
    if sys.platform == 'win32':
        subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "src/dashboard/app.py",
             "--server.headless", "true",
             "--server.port", "8501",
             "--browser.gatherUsageStats", "false"],
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    else:
        subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "src/dashboard/app.py",
             "--server.headless", "true",
             "--server.port", "8501",
             "--browser.gatherUsageStats", "false"],
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )

def main():
    print("=" * 60)
    print("  🎯 OPTION BUYER INTELLIGENCE - DESKTOP APP")
    print("=" * 60)
    
    # Check if Streamlit is already running
    if not is_port_open(8501):
        print("\n[1/3] Starting data collector...")
        start_collector()
        time.sleep(2)
        
        print("[2/3] Starting dashboard server...")
        start_streamlit()
        time.sleep(6)  # Wait for Streamlit to boot
    else:
        print("\n✅ Dashboard already running on port 8501")
    
    print("[3/3] Opening desktop window...\n")
    print("Close this window to stop the app.\n")
    
    # Create desktop window
    window = webview.create_window(
        title="🎯 Option Buyer Intelligence",
        url="http://localhost:8501",
        width=1440,
        height=900,
        resizable=True,
        fullscreen=False,
        min_size=(1100, 700),
        background_color='#0a1628'
    )
    
    webview.start()

if __name__ == "__main__":
    main()