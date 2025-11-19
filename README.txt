========================================
  DATA MASKING TOOL - INSTALLATION
========================================

This tool helps you mask sensitive identifiers in your datasets and restore them when needed.

REQUIREMENTS:
-------------
- Python 3.8 or higher
- Internet connection (for first-time setup only)

QUICK START:
-----------
1. Extract all files to a folder on your computer

2. Double-click the appropriate launcher:
   - Windows: run_windows.bat
   - Mac/Linux: run_mac_linux.sh
   
3. Wait for the setup to complete (first time only)

4. Your browser will open automatically to http://localhost:8501

5. Start using the tool!

WHAT HAPPENS ON FIRST RUN:
--------------------------
The launcher will:
✓ Check if Python is installed
✓ Create a virtual environment (keeps dependencies isolated)
✓ Install required packages (streamlit, pandas, openpyxl)
✓ Launch the application
✓ Open your browser automatically

SUBSEQUENT RUNS:
---------------
After the first setup, launching is instant - just double-click the launcher!

TROUBLESHOOTING:
---------------

Problem: "Python is not installed" error
Solution: 
  1. Download Python from https://www.python.org/downloads/
  2. During installation, CHECK "Add Python to PATH"
  3. Restart your computer
  4. Try running the launcher again

Problem: Browser doesn't open automatically
Solution: Manually open your browser and go to http://localhost:8501

Problem: Port 8501 already in use
Solution: Close any other Streamlit applications or restart your computer

Problem: (Mac/Linux) Permission denied
Solution: Open Terminal in this folder and run:
  chmod +x run_mac_linux.sh
  ./run_mac_linux.sh

STOPPING THE APPLICATION:
------------------------
- Close the browser tab
- In the command window, press Ctrl+C
- Close the command window

SHARING WITH OTHERS:
-------------------
Simply zip the entire folder and share it. Each user runs their own local copy.

SECURITY NOTE:
-------------
- This tool runs LOCALLY on your computer
- No data is uploaded to any server
- Keep your mapping files (masking_map.json) secure
- Store mapping files separately from masked data

SUPPORT:
-------
For issues or questions, contact [nabdulmutallib@company.com]

========================================
