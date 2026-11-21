@echo off
cd /d "%~dp0"
where pythonw >nul 2>nul && (start "" pythonw launcher.py & exit /b)
where py >nul 2>nul && (start "" py -3 launcher.py & exit /b)
python launcher.py
if errorlevel 1 pause
