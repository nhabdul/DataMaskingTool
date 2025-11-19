import subprocess
import sys
import os

def main():
    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_path = os.path.dirname(sys.executable)
    else:
        # Running as script
        app_path = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the Streamlit app
    streamlit_app = os.path.join(app_path, 'data_masking_tool.py')
    
    # Run Streamlit
    subprocess.run(['streamlit', 'run', streamlit_app])

if __name__ == "__main__":
    main()