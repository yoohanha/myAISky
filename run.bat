@echo off
REM myAISky FastAPI Server 실행 스크립트

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║           myAISky 2.0 - FastAPI + SQLite Backend              ║
echo ║              AI Weather & Agent Monitoring Dashboard           ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Python 버전 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo 🔗 https://www.python.org 에서 Python을 설치하세요.
    pause
    exit /b 1
)

REM 의존성 설치 확인
echo 📦 의존성 설치 확인 중...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 📥 필수 패키지를 설치하는 중입니다...
    pip install -r requirements.txt
)

echo.
echo 🚀 FastAPI 서버를 시작합니다...
echo.
echo 📊 대시보드 주소: http://localhost:8000
echo 🌤️  기상 API 주소: http://localhost:8000/api/weather
echo 📦 DB 조회 주소: http://localhost:8000/api/weather/logs
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo.

REM uvicorn 서버 실행
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

pause
