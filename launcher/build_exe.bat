@echo off
chcp 65001 >nul
REM Windows용 단일 실행 파일(SOVIX Launcher.exe) 빌드
cd /d "%~dp0"
python -m pip install --upgrade pyinstaller || goto :fail
python -m PyInstaller --noconfirm --onedir --windowed --name "SOVIX Launcher" ^
  --add-data "content.json;." --add-data "demo_game.py;." launcher.py || goto :fail
echo.
echo 완료: dist\SOVIX Launcher\SOVIX Launcher.exe
pause
exit /b 0
:fail
echo 빌드 실패
pause
exit /b 1
