"""
myAISky Backend - FastAPI + SQLite
AI Weather & Agent Monitoring Dashboard
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.requests import Request
import requests
import sqlite3
from datetime import datetime
from pathlib import Path
import json

# ==================== 설정 ====================
app = FastAPI(title="myAISky Backend", version="2.0.0")

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
DB_DIR = Path(__file__).parent / "database"
DB_PATH = DB_DIR / "weather_logs.db"

# 디렉토리 생성
DB_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# StaticFiles 마운트 (이미지, CSS 등)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Jinja2 템플릿 설정
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ==================== 데이터베이스 ====================

def init_db():
    """SQLite 데이터베이스 초기화"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL NOT NULL,
            humidity INTEGER,
            wind_speed REAL,
            apparent_temperature REAL,
            condition TEXT,
            location TEXT DEFAULT 'Seoul, South Korea',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ 데이터베이스 초기화 완료: {DB_PATH}")


def insert_weather_log(temperature, humidity, wind_speed, apparent_temperature, condition, location="Seoul, South Korea"):
    """기상 데이터를 DB에 저장"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO weather_logs
            (temperature, humidity, wind_speed, apparent_temperature, condition, location)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (temperature, humidity, wind_speed, apparent_temperature, condition, location))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB 저장 오류: {e}")
        return False


def get_weather_logs(limit=50):
    """최근 기상 데이터 조회"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM weather_logs
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        print(f"DB 조회 오류: {e}")
        return []


def get_weather_logs_count():
    """저장된 기상 데이터 개수 조회"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM weather_logs')
        count = cursor.fetchone()[0]
        conn.close()

        return count
    except Exception as e:
        print(f"DB 카운트 오류: {e}")
        return 0

# ==================== 기상 API ====================

def get_weather_data():
    """Open-Meteo API에서 기상 데이터 조회"""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 37.5665,
            "longitude": 126.9780,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
            "timezone": "Asia/Seoul"
        }

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        return {
            "location": "Seoul, South Korea",
            "timestamp": current.get("time"),
            "temperature": current.get("temperature_2m", 0),
            "apparent_temperature": current.get("apparent_temperature", 0),
            "humidity": current.get("relative_humidity_2m", 0),
            "wind_speed": current.get("wind_speed_10m", 0),
            "weather_code": current.get("weather_code", 0),
            "status": "OK"
        }
    except requests.exceptions.RequestException as e:
        print(f"날씨 API 오류: {e}")
        return {
            "location": "Seoul, South Korea",
            "temperature": 18.5,
            "apparent_temperature": 17.2,
            "humidity": 65,
            "wind_speed": 3.5,
            "status": "FALLBACK_MODE",
            "message": "실시간 데이터 로드 불가 - 캐시 데이터 표시"
        }


# 기상 데이터 캐시
weather_cache = None
cache_timestamp = None


# ==================== API 엔드포인트 ====================

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """대시보드 메인 페이지"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/weather")
async def get_weather():
    """기상 데이터 조회 및 DB 저장"""
    global weather_cache, cache_timestamp

    weather_data = get_weather_data()

    # DB에 저장
    if weather_data["status"] == "OK":
        insert_weather_log(
            temperature=weather_data["temperature"],
            humidity=weather_data["humidity"],
            wind_speed=weather_data["wind_speed"],
            apparent_temperature=weather_data["apparent_temperature"],
            condition=f"Code: {weather_data.get('weather_code', 'N/A')}",
            location=weather_data["location"]
        )

    weather_cache = weather_data
    cache_timestamp = datetime.now()

    return weather_data


@app.get("/api/weather/logs")
async def get_weather_logs_endpoint():
    """데이터베이스에 저장된 기상 데이터 조회"""
    try:
        logs = get_weather_logs(limit=50)
        count = get_weather_logs_count()

        return {
            "count": count,
            "logs": logs,
            "status": "OK"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/weather/logs/count")
async def get_logs_count():
    """저장된 데이터 개수"""
    count = get_weather_logs_count()
    return {"count": count}


@app.get("/api/stats")
async def get_stats():
    """통계 정보"""
    logs = get_weather_logs(limit=100)

    if not logs:
        return {"status": "NO_DATA"}

    temperatures = [float(log["temperature"]) for log in logs if log["temperature"]]

    return {
        "total_records": get_weather_logs_count(),
        "avg_temperature": round(sum(temperatures) / len(temperatures), 1) if temperatures else 0,
        "max_temperature": round(max(temperatures), 1) if temperatures else 0,
        "min_temperature": round(min(temperatures), 1) if temperatures else 0,
        "latest_record": logs[0] if logs else None
    }


@app.get("/api/health")
async def health_check():
    """서버 상태 체크"""
    db_count = get_weather_logs_count()
    return {
        "status": "OK",
        "database": "CONNECTED",
        "db_records": db_count,
        "timestamp": datetime.now().isoformat()
    }


# ==================== 서버 시작 ====================

if __name__ == "__main__":
    # 데이터베이스 초기화
    init_db()

    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║           myAISky 2.0 - FastAPI + SQLite Backend              ║
    ║              AI Weather & Agent Monitoring Dashboard           ║
    ╚════════════════════════════════════════════════════════════════╝

    📊 대시보드 주소: http://localhost:8000
    🌤️  기상 API 주소: http://localhost:8000/api/weather
    📦 DB 조회 주소: http://localhost:8000/api/weather/logs
    💻 상태 체크: http://localhost:8000/api/health

    📁 프로젝트 구조:
       ├── backend/main.py (FastAPI 백엔드)
       ├── backend/database/weather_logs.db (SQLite)
       ├── frontend/templates/index.html (UI)
       ├── frontend/static/sky.jpg (배경)
       └── requirements.txt

    ▶️  서버 실행 명령어:
       uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

    🔗 브라우저에서 http://localhost:8000 으로 접속하세요.

    ╔════════════════════════════════════════════════════════════════╗
    """)

    # Uvicorn 서버 실행
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
