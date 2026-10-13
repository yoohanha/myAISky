# myAISky 2.0 - AI Weather & Agent Monitoring Dashboard

FastAPI + SQLite + 기상청 공공 API를 활용한 실시간 날씨 모니터링 대시보드

## 🚀 빠른 시작

### 방법 1: run.bat (Windows)
```bash
# 프로젝트 폴더에서
run.bat
```
더블클릭하거나 cmd에서 실행하면 자동으로 서버가 시작됩니다.

### 방법 2: run_simple.bat (간단한 버전)
```bash
run_simple.bat
```

### 방법 3: PowerShell 스크립트
```powershell
.\run.ps1
```

### 방법 4: 직접 명령 실행
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## 🌐 접속 주소

서버가 시작되면 브라우저에서 다음 주소로 접속하세요:

| 주소 | 설명 |
|------|------|
| http://localhost:8000 | 대시보드 |
| http://localhost:8000/api/weather | 실시간 기상 데이터 (JSON) |
| http://localhost:8000/api/weather/logs | 저장된 기상 데이터 |
| http://localhost:8000/api/stats | 기상 데이터 통계 |
| http://localhost:8000/api/health | 서버 상태 |

## 📦 프로젝트 구조

```
myAISky/
├── backend/
│   ├── main.py                 # FastAPI 백엔드 + SQLite 연동
│   └── database/
│       └── weather_logs.db     # SQLite 데이터베이스 (자동 생성)
├── frontend/
│   ├── templates/
│   │   └── index.html          # 대시보드 UI
│   └── static/
│       └── sky.jpg             # 배경 이미지
├── run.bat                      # Windows 배치 스크립트
├── run_simple.bat               # 간단한 버전
├── run.ps1                      # PowerShell 스크립트
├── requirements.txt             # Python 의존성
├── .gitignore                   # Git 제외 파일
└── README.md                    # 이 파일
```

## 🌤️ 기상청 API 연동

### 실시간 기상 데이터
- **API**: 기상청 VilageFcstInfoService_2.0 초단기실황조회
- **위치**: 서울 (격자 좌표: nx=55, ny=127)
- **정보**: 실시간 기온, 습도, 풍속, 강수형태

### 데이터 소스
1. **1순위**: 기상청 공공 API (실제 데이터)
2. **2순위**: Open-Meteo API (기상청 실패 시)
3. **3순위**: 캐시 데이터 (모두 실패 시)

## 💾 SQLite 데이터베이스

### weather_logs 테이블
```
┌─ id (INTEGER PRIMARY KEY)
├─ temperature (REAL) - 기온
├─ humidity (INTEGER) - 습도
├─ wind_speed (REAL) - 풍속
├─ apparent_temperature (REAL) - 체감온도
├─ condition (TEXT) - 날씨 상태
├─ location (TEXT) - 위치
└─ timestamp (DATETIME) - 기록 시간
```

### 자동 저장
- `/api/weather` 조회 시 자동으로 DB에 저장
- 기상청 실시간 데이터 기록

## 🎨 대시보드 기능

### 실시간 데이터 표시
- ✅ 현재 온도
- ✅ 습도
- ✅ 풍속
- ✅ 체감온도
- ✅ 날씨 상태 (맑음, 비, 눈 등)
- ✅ 데이터 소스 (기상청/Open-Meteo/캐시)

### 수동 제어 패널
- 🔄 **기상 데이터 동기화** - 최신 데이터 조회
- 📊 **DB 데이터 조회** - 저장된 데이터 확인
- 📄 **리포트 생성** - 현재 기상 리포트 생성
- 💾 **데이터 내보내기** - JSON 파일로 저장

### AI 에이전트 실시간 로그
- 시스템 이벤트 실시간 표시
- 데이터 소스별 상태 메시지

## 📋 API 엔드포인트

### GET /api/weather
실시간 기상 데이터 조회 및 DB 저장

**응답 예시:**
```json
{
  "location": "Seoul, South Korea",
  "timestamp": "2026-10-13 18:15",
  "temperature": 18.5,
  "humidity": 65,
  "wind_speed": 3.2,
  "apparent_temperature": 18.5,
  "condition": "맑음",
  "source": "Korea Meteorological Administration (KMA)",
  "status": "OK"
}
```

### GET /api/weather/logs
저장된 기상 데이터 조회

**응답 예시:**
```json
{
  "count": 15,
  "logs": [
    {
      "id": 1,
      "temperature": 18.5,
      "humidity": 65,
      "wind_speed": 3.2,
      "condition": "맑음",
      "timestamp": "2026-10-13 18:15"
    }
  ],
  "status": "OK"
}
```

### GET /api/stats
기상 데이터 통계

**응답 예시:**
```json
{
  "total_records": 15,
  "avg_temperature": 18.2,
  "max_temperature": 22.5,
  "min_temperature": 15.8,
  "latest_record": {...}
}
```

### GET /api/health
서버 상태 확인

**응답 예시:**
```json
{
  "status": "OK",
  "database": "CONNECTED",
  "db_records": 15,
  "timestamp": "2026-10-13T18:15:00"
}
```

## ⚙️ 설정

### requirements.txt
필요한 Python 패키지:
```
fastapi==0.104.1
uvicorn==0.24.0
requests==2.31.0
pydantic==2.5.0
python-dotenv==1.0.0
Jinja2==3.1.2
```

### 환경 변수
프로젝트 루트에 `.env` 파일 생성 (선택사항):
```
# 포트 변경
PORT=8000

# 호스트 변경
HOST=0.0.0.0

# 기타 설정
DEBUG=True
```

## 🔧 트러블슈팅

### run.bat가 실행되지 않는 경우

**해결 방법:**
1. **PowerShell 스크립트 사용**
   ```powershell
   .\run.ps1
   ```

2. **직접 명령 실행**
   ```bash
   python -m pip install -r requirements.txt
   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Python 경로 확인**
   ```bash
   where python
   where pip
   ```

4. **포트 충돌 확인**
   - 포트 8000이 이미 사용 중인 경우, 다른 포트 사용:
   ```bash
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
   ```

### Python이 설치되지 않은 경우
- https://www.python.org 에서 Python 설치
- Windows에서는 PATH에 Python 추가되었는지 확인

### 의존성 설치 실패
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 📝 라이선스

MIT License

## 👨‍💻 개발자

Created with ❤️ by Claude

## 📞 지원

문제가 발생하면:
1. 터미널 에러 메시지 확인
2. 위의 트러블슈팅 섹션 참고
3. GitHub Issues에 보고

---

**Happy Weather Monitoring! 🌤️**
