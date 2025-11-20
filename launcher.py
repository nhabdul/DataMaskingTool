import sys
import os

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    
    import streamlit.web.cli as stcli
    
    # Get the correct path to the app
    if getattr(sys, 'frozen', False):
        script_dir = sys._MEIPASS
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    
    script_path = os.path.join(script_dir, 'data_masking_tool.py')
    
    # Create a Streamlit config file to disable dev mode
    config_dir = os.path.join(os.path.expanduser("~"), ".streamlit")
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, "config.toml")
    with open(config_path, 'w') as f:
        f.write('[global]\n')
        f.write('developmentMode = false\n')
        f.write('[server]\n')
        f.write('port = 8501\n')
        f.write('headless = true\n')
        f.write('[browser]\n')
        f.write('gatherUsageStats = false\n')
    
    # Run Streamlit without port argument (it will use config file)
    sys.argv = [
        "streamlit",
        "run",
        script_path
    ]
    
    print("=" * 60)
    print("  DATA MASKING TOOL")
    print("=" * 60)
    print("\nStarting application...")
    print("Open your browser to: http://localhost:8501")
    print("\nKEEP THIS WINDOW OPEN")
    print("Press Ctrl+C to stop\n")
    print("=" * 60)
    
    sys.exit(stcli.main())
