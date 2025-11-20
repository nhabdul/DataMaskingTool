import sys
import os

# Must be at the very top for PyInstaller
if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    
    # Import after freeze_support
    import streamlit.web.cli as stcli
    
    # Get the correct path to the app
    if getattr(sys, 'frozen', False):
        script_dir = sys._MEIPASS
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    
    script_path = os.path.join(script_dir, 'data_masking_tool.py')
    
    # Run Streamlit
    sys.argv = [
        "streamlit",
        "run",
        script_path,
        "--server.port=8501",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.address=localhost"
    ]
    
    sys.exit(stcli.main())
