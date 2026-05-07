@echo off
echo Packaging the Scheduler application...
echo Verifying dependencies...
python -m pip install -r requirements.txt
python -m PyInstaller --noconsole --onefile main.py
echo Build complete! Check the 'dist' directory for your executable.
pause