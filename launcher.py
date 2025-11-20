import os
import sys
import subprocess
import socket
import time
import webbrowser
from threading import Timer
import multiprocessing

def find_free_port():
    """Find a free port to run Streamlit on."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def open_browser(port):
    """Open browser after a delay."""
    time.sleep(5)
    webbrowser.open(f'http://localhost:{port}')

def main():
    # CRITICAL: Prevent multiprocessing issues with frozen executables
    multiprocessing.freeze_support()
    
    # Get the directory where files are located
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    script_path = os.path.join(application_path, 'data_masking_tool.py')
    
    # Check if file exists
    if not os.path.exists(script_path):
        print(f"ERROR: Cannot find {script_path}")
        input("Press Enter to exit...")
        return
    
    port = find_free_port()
    
    print("=" * 60)
    print("  DATA MASKING TOOL")
    print("=" * 60)
    print(f"\nStarting on http://localhost:{port}")
    print("\nKEEP THIS WINDOW OPEN")
    print("Browser will open in 5 seconds...")
    print("Press Ctrl+C to stop\n")
    print("=" * 60)
    
    # Open browser once
    Timer(5, open_browser, args=[port]).start()
    
    try:
        # Create a new environment to prevent issues
        env = os.environ.copy()
        env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        
        streamlit_cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            script_path,
            f"--server.port={port}",
            "--server.headless=true",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false",
            "--browser.serverAddress=localhost",
            f"--browser.serverPort={port}",
            "--browser.gatherUsageStats=false"
        ]
        
        subprocess.run(streamlit_cmd, env=env, check=True)
        
    except KeyboardInterrupt:
        print("\n\nStopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
