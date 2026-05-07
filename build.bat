@echo off
echo Packaging the Scheduler application...

echo Cleaning old builds...
rmdir /s /q build
rmdir /s /q dist
del *.spec

echo Installing dependencies...
python -m pip install -r requirements.txt

echo Building executable...
python -m PyInstaller ^
--noconsole ^
--onedir ^
--name Scheduler ^
--clean ^
--collect-all PyQt6 ^
scheduler_app\src\main.py

echo Build complete! Check the 'dist' directory.
pause
