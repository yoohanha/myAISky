# myAISky FastAPI Server 실행 스크립트 (PowerShell)

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  myAISky 2.0 - FastAPI + SQLite Backend" -ForegroundColor Cyan
Write-Host "  AI Weather Agent Monitoring Dashboard" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 현재 디렉토리로 이동
Set-Location -Path $PSScriptRoot

# Python 확인
Write-Host "[INFO] Python 확인 중..." -ForegroundColor Yellow
$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python이 설치되지 않았습니다." -ForegroundColor Red
    Write-Host "https://www.python.org 에서 Python을 설치하세요." -ForegroundColor Red
    Read-Host "계속하려면 Enter를 누르세요"
    exit 1
}
Write-Host "Python 설치됨: $pythonCheck" -ForegroundColor Green

# 의존성 확인 및 설치
Write-Host ""
Write-Host "[INFO] 의존성 설치 확인 중..." -ForegroundColor Yellow
$fastapi = python -m pip show fastapi 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[INFO] 필수 패키지를 설치하는 중입니다..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] 패키지 설치 실패" -ForegroundColor Red
        Read-Host "계속하려면 Enter를 누르세요"
        exit 1
    }
}
Write-Host "의존성 설치 확인 완료" -ForegroundColor Green

# 서버 시작
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  FastAPI 서버 시작 중..." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Dashboard URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Weather API: http://localhost:8000/api/weather" -ForegroundColor Cyan
Write-Host "DB Logs: http://localhost:8000/api/weather/logs" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] 서버를 중지하려면 Ctrl+C를 누르세요." -ForegroundColor Yellow
Write-Host ""

# uvicorn 서버 실행
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] 서버 실행 실패" -ForegroundColor Red
    Write-Host ""
    Read-Host "계속하려면 Enter를 누르세요"
}
