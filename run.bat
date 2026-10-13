@echo off
REM myAISky FastAPI Server 실행 스크립트
chcp 65001 > nul

REM 현재 디렉토리로 이동
cd /d "%~dp0"

echo.
echo ============================================================
echo   myAISky 2.0 - FastAPI + SQLite Backend
echo   AI Weather Agent Monitoring Dashboard
echo ============================================================
echo.

REM Python 버전 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되지 않았습니다.
    echo 다음 링크에서 Python을 설치하세요:
    echo https://www.python.org
    echo.
    pause
    exit /b 1
)

REM Python 버전 출력
python --version

REM 의존성 설치 확인
echo.
echo [INFO] 의존성 설치 확인 중...
python -m pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [INFO] 필수 패키지를 설치하는 중입니다...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] 패키지 설치 실패
        echo 콘솔 창을 닫으려면 아무 키나 누르세요.
        pause
        exit /b 1
    )
)

echo.
echo ============================================================
echo   FastAPI 서버 시작 중...
echo ============================================================
echo.
echo Dashboard: http://localhost:8000
echo Weather API: http://localhost:8000/api/weather
echo DB Logs: http://localhost:8000/api/weather/logs
echo.
echo [INFO] 서버를 중지하려면 Ctrl+C를 누르세요.
echo.

REM uvicorn 서버 실행
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

if errorlevel 1 (
    echo.
    echo [ERROR] 서버 실행 실패
    echo.
    pause
)
else (
    pause
)
