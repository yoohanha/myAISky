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
from datetime import datetime, timedelta
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import urllib.parse

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

# 기상청 API 설정
KMA_API_KEY = "c8537ba5d54f1d34c5829f2626eab25672932c12bfbe77ed1ac0eebf8182ed1"
KMA_API_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
SEOUL_NX = 55  # 서울 격자 X 좌표
SEOUL_NY = 127  # 서울 격자 Y 좌표

# 강수형태 코드 변환
PTY_CODES = {
    "0": "맑음",
    "1": "비",
    "2": "비/눈",
    "3": "눈",
    "4": "소나기",
    "5": "빗소나기",
    "6": "눈소나기",
    "7": "폭우"
}


def get_kma_weather_data():
    """기상청 초단기실황조회 API에서 실시간 날씨 데이터 조회"""
    try:
        # 현재 시간 기준 base_date, base_time 계산
        now = datetime.now()

        # API는 가장 최근의 발표 시간 데이터를 제공
        # 시간이 정각 45분 이전이면 이전 시간 데이터 사용
        if now.minute < 45:
            now = now - timedelta(hours=1)

        base_date = now.strftime("%Y%m%d")
        base_time = now.strftime("%H") + "00"

        params = {
            "serviceKey": KMA_API_KEY,
            "pageNo": "1",
            "numOfRows": "60",
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": str(SEOUL_NX),
            "ny": str(SEOUL_NY)
        }

        response = requests.get(KMA_API_URL, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()

        # API 응답 검증
        if data.get("response", {}).get("header", {}).get("resultCode") != "00":
            raise Exception(f"API 오류: {data.get('response', {}).get('header', {}).get('resultMsg')}")

        # 데이터 추출
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

        if not items:
            raise Exception("날씨 데이터 없음")

        # 카테고리별 데이터 정렬
        weather_data = {}
        for item in items:
            category = item.get("category")
            value = item.get("obsrValue")

            if category == "T1H":  # 기온
                weather_data["temperature"] = float(value)
            elif category == "REH":  # 습도
                weather_data["humidity"] = int(float(value))
            elif category == "WSD":  # 풍속
                weather_data["wind_speed"] = float(value)
            elif category == "PTY":  # 강수형태
                weather_data["condition"] = PTY_CODES.get(value, f"기타({value})")

        # 필수 데이터 확인
        if "temperature" not in weather_data:
            weather_data["temperature"] = 0
        if "humidity" not in weather_data:
            weather_data["humidity"] = 0
        if "wind_speed" not in weather_data:
            weather_data["wind_speed"] = 0
        if "condition" not in weather_data:
            weather_data["condition"] = "데이터 없음"

        return {
            "location": "Seoul, South Korea",
            "timestamp": f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:8]} {base_time[:2]}:{base_time[2:]}",
            "temperature": weather_data.get("temperature", 0),
            "humidity": weather_data.get("humidity", 0),
            "wind_speed": weather_data.get("wind_speed", 0),
            "apparent_temperature": weather_data.get("temperature", 0),  # 기상청에서 체감온도 직접 제공 안함
            "condition": weather_data.get("condition", "알 수 없음"),
            "source": "Korea Meteorological Administration (KMA)",
            "status": "OK"
        }

    except Exception as e:
        print(f"기상청 API 오류: {e}")
        return None


def get_weather_data():
    """기상청 공공 API를 우선 사용하여 실시간 기상 데이터 조회"""
    # 기상청 API 우선 사용
    kma_data = get_kma_weather_data()
    if kma_data:
        return kma_data

    # 기상청 API 실패 시 캐시 데이터 반환
    print("[WARNING] 기상청 API 실패 - 캐시 데이터 사용")
    return {
        "location": "Seoul, South Korea",
        "temperature": 18.5,
        "apparent_temperature": 17.2,
        "humidity": 65,
        "wind_speed": 3.5,
        "condition": "데이터 로드 중",
        "source": "Korea Meteorological Administration (KMA)",
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
            condition=weather_data.get("condition", "알 수 없음"),  # 기상청 날씨 상태 저장
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
