import os
import sys
import subprocess
import socket
import time
import webbrowser
from threading import Timer

def find_free_port():
    """Find a free port to run Streamlit on."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def open_browser(port):
    """Open browser after a delay."""
    time.sleep(3)
    webbrowser.open(f'http://localhost:{port}')

def main():
    # Get the directory where files are located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable - PyInstaller extracts to _MEIPASS
        application_path = sys._MEIPASS
    else:
        # Running as script
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the main app
    script_path = os.path.join(application_path, 'data_masking_tool.py')
    
    # Find a free port
    port = find_free_port()
    
    print("=" * 60)
    print("  DATA MASKING TOOL")
    print("=" * 60)
    print(f"\nStarting application on port {port}...")
    print(f"Opening browser to http://localhost:{port}")
    print("\nKEEP THIS WINDOW OPEN while using the app")
    print("Press Ctrl+C to stop\n")
    print("=" * 60)
    
    # Open browser in background
    Timer(3, open_browser, args=[port]).start()
    
    # Run Streamlit using Python's subprocess
    try:
        streamlit_cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            script_path,
            f"--server.port={port}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false"
        ]
        
        subprocess.run(streamlit_cmd)
    except KeyboardInterrupt:
        print("\n\nApplication stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        print(f"Script path: {script_path}")
        print(f"Application path: {application_path}")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
