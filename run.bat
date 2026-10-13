@echo off
cd /d "%~dp0"
echo ============================================================
echo myAISky FastAPI Server Starting...
echo ============================================================
echo.

:: Check and install requirements if needed
python -m pip show fastapi >nul 2>&1
if errorlevel 1 (
    python -m pip install -r requirements.txt
)

echo Server is running on http://127.0.0.1:8001
start http://127.0.0.1:8001

python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
pause