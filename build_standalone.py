"""
CREATING STANDALONE EXECUTABLE WITH PYINSTALLER
-----------------------------------------------

1. Install PyInstaller:
   pip install pyinstaller

2. Save this as build_standalone.py and run:
   python build_standalone.py

3. Find the executable in the "dist" folder

NOTE: This creates a large file (100-200MB) but users won't need Python installed.
"""

import os
import subprocess
import sys

def build_executable():
    print("Building standalone executable...")
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',                    # Single executable file
        '--windowed',                   # No console window
        '--name=DataMaskingTool',       # Executable name
        '--add-data=data_masking_tool.py:.',  # Include the main script
        '--hidden-import=streamlit',
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--collect-all=streamlit',
        'launcher.py'                   # Main entry point
    ]
    
    subprocess.run(cmd, check=True)
    print("\n✅ Build complete! Check the 'dist' folder for the executable.")

if __name__ == "__main__":
    build_executable()
