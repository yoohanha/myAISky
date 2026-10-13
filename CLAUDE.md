# myAISky Development Rules & Guidelines

myAISky 프로젝트의 일관된 개발 및 유지보수를 위한 핵심 개발 규칙입니다.
모든 개발자는 아래 규칙을 반드시 준수하여야 합니다.

---

## 1. 기상청 API 연동 및 데이터 파싱 룰

### 1.1 API 호출 표준
- **API Endpoint**: `https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst`
- **인증키**: `c8537ba5d54f1d34c5829f2626eab25672932c12bfbe77ed1ac0eebf8182ed1`
- **위치**: 서울 기준 격자 좌표 (nx=55, ny=127)
- **데이터 타입**: JSON
- **갱신 주기**: 약 30분~1시간

### 1.2 데이터 파싱 안전 규칙
```python
# ✅ 올바른 예시
try:
    response = requests.get(KMA_API_URL, params=params, timeout=5)
    response.raise_for_status()
    
    data = response.json()
    
    # 안전한 중첩 구조 접근
    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    
    if not items:
        raise Exception("기상 데이터 없음")
    
    # 카테고리별 데이터 추출
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
            weather_data["condition"] = convert_pty_code(value)
    
    return weather_data
    
except Exception as e:
    logger.error(f"기상청 API 파싱 오류: {e}")
    return None
```

### 1.3 주요 기상 지표 추출 규칙

| 카테고리 | 코드 | 설명 | 필수 여부 |
|---------|------|------|---------|
| 기온 | `T1H` | 기온(℃) | ✅ 필수 |
| 습도 | `REH` | 상대습도(%) | ✅ 필수 |
| 풍속 | `WSD` | 풍속(m/s) | ✅ 필수 |
| 강수형태 | `PTY` | 강수형태 코드 | ✅ 필수 |
| 낙뢰 | `LGT` | 낙뢰 | ⭕ 선택 |

**필수 지표 누락 시 처리:**
- `temperature`가 없으면 기본값 0.0 사용
- `humidity`가 없으면 기본값 0 사용
- `wind_speed`가 없으면 기본값 0.0 사용
- `condition`이 없으면 "알 수 없음" 표시

### 1.4 강수형태(PTY) 코드 변환 테이블
```python
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
```

### 1.5 데이터 출처 표시 규칙
- 모든 API 응답에서 `source` 필드는 반드시 포함할 것
- `source` 값은 항상 다음 중 하나여야 함:
  - **정상 데이터**: `"Korea Meteorological Administration (KMA)"`
  - **폴백 캐시**: `"Korea Meteorological Administration (KMA)"` (동일하게 유지)
- Open-Meteo 등 다른 API는 사용하지 말 것

---

## 2. SQLite 데이터베이스(`weather_logs.db`) 적재 룰

### 2.1 데이터베이스 초기화
```python
def init_db():
    """SQLite 데이터베이스 초기화 - 서버 시작 시 필수 호출"""
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
```

### 2.2 데이터 저장 규칙
- **저장 시점**: 기상청 API 조회 직후, `status == "OK"`일 때만 저장
- **필드 매핑**:
  - `temperature`: 기온 (실수형)
  - `humidity`: 습도 (정수형, %)
  - `wind_speed`: 풍속 (실수형, m/s)
  - `apparent_temperature`: 체감온도 (실수형)
  - `condition`: 날씨 상태 (문자형, 한글)
  - `location`: 위치 (기본값: "Seoul, South Korea")
  - `timestamp`: 기록 시간 (자동 현재 시간)

### 2.3 안전한 INSERT 패턴
```python
def insert_weather_log(temperature, humidity, wind_speed, 
                       apparent_temperature, condition, 
                       location="Seoul, South Korea"):
    """기상 데이터를 DB에 안전하게 저장"""
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
        
        logger.info(f"DB 저장 성공: 온도={temperature}°C, 상태={condition}")
        return True
        
    except Exception as e:
        logger.error(f"DB 저장 오류: {e}")
        return False
```

### 2.4 테이블 존재성 검증
- 서버 시작 시 `init_db()` 반드시 호출
- `CREATE TABLE IF NOT EXISTS` 패턴 사용으로 기존 테이블 보존
- 마이그레이션 필요 시 별도 버전 관리

### 2.5 데이터 조회 규칙
- 조회 시 `SELECT * FROM weather_logs ORDER BY timestamp DESC` 사용
- 페이징 시 `LIMIT` 절 반드시 사용 (기본값: 50)
- 통계 조회 시 NULL 값 안전하게 처리

---

## 3. AI 에이전트 로그 및 응답 포맷 룰

### 3.1 실시간 로그 출력 포맷 표준
```
[시간] 🌡️ 기상청(KMA) 데이터 동기화 완료 - Seoul, South Korea
[시간] 📦 데이터베이스에서 25개의 기상 데이터 로드 완료
[시간] ✅ 신규 데이터 저장 완료 (온도: 18.5°C, 상태: 맑음)
[시간] ⚠️ 기상청 실시간 데이터 로드 중 - 캐시 데이터 표시
[시간] ❌ 기상 데이터 로드 실패
```

### 3.2 로그 포맷 규칙
```python
# 형식: [시간] 이모지 메시지 - 위치 (출처)

# ✅ 올바른 예시
addLog('🌡️ 기상청(KMA) 데이터 동기화 완료 - Seoul, South Korea');
addLog('📦 데이터베이스에서 25개의 기상 데이터 로드 완료');
addLog('✅ 신규 기상 데이터 저장 완료');

# ❌ 잘못된 예시
addLog('데이터 동기화 완료');  # 이모지 누락
addLog('기상청 API 호출 성공');  # 상세 정보 누락
```

### 3.3 백엔드 API 응답 표준 스키마

#### 성공 응답
```json
GET /api/weather

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

#### 캐시 폴백 응답
```json
{
  "location": "Seoul, South Korea",
  "temperature": 18.5,
  "humidity": 65,
  "wind_speed": 3.5,
  "condition": "데이터 로드 중",
  "source": "Korea Meteorological Administration (KMA)",
  "status": "FALLBACK_MODE",
  "message": "실시간 데이터 로드 불가 - 캐시 데이터 표시"
}
```

### 3.4 DB 조회 응답 포맷
```json
GET /api/weather/logs

{
  "count": 25,
  "logs": [
    {
      "id": 1,
      "temperature": 18.5,
      "humidity": 65,
      "wind_speed": 3.2,
      "condition": "맑음",
      "location": "Seoul, South Korea",
      "timestamp": "2026-10-13 18:15"
    }
  ],
  "status": "OK"
}
```

### 3.5 에러 응답 규칙
```json
{
  "status": "ERROR",
  "message": "기상청 API 요청 실패",
  "error_code": "API_TIMEOUT",
  "timestamp": "2026-10-13T18:15:00"
}
```

---

## 4. 프론트엔드 개발 규칙

### 4.1 데이터 소스 표시 규칙
- 모든 날씨 데이터 표시 시 데이터 소스를 명확히 표시
- 기상청 데이터: `🇰🇷 Korea Meteorological Administration (KMA)`
- 다른 출처 사용 금지

### 4.2 실시간 업데이트 규칙
- 기본 갱신 주기: 10분 (600,000ms)
- 수동 갱신: "기상 데이터 동기화" 버튼으로만 제공
- 자동 갱신 중 사용자가 조작했다면 상태 메시지 표시

### 4.3 에러 처리 규칙
```javascript
// ✅ 올바른 에러 처리
try {
    const response = await fetch('/api/weather');
    const data = await response.json();
    
    if (response.ok) {
        updateDashboard(data);
        addLog('🌡️ 기상청(KMA) 데이터 동기화 완료 - ' + data.location);
    } else {
        addLog('❌ 기상 데이터 로드 실패');
    }
} catch (error) {
    console.error('오류:', error);
    addLog('❌ 기상 데이터 로드 실패');
}
```

---

## 5. Git 커밋 메시지 규칙

### 5.1 커밋 메시지 형식
```
<type>: <subject>

<body>

<footer>
```

### 5.2 Type 규칙
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `refactor`: 코드 재구성 (기능 변화 없음)
- `docs`: 문서 변경
- `style`: 코드 포맷 변경
- `perf`: 성능 개선
- `test`: 테스트 추가

### 5.3 Subject 규칙
- 명령형으로 작성 (예: "Fix", "Add" - "Fixed", "Added" X)
- 마침표 사용 금지
- 한글 또는 영문으로 일관되게 작성

### 5.4 Body 규칙
- 무엇을 변경했는지 명확히 설명
- Why와 How를 포함
- 여러 항목은 bullet point 사용

### 5.5 예시
```
refactor: 기상청 API 단일화 - Open-Meteo 의존성 제거

기상청 공공 API를 주요 데이터 소스로 확정
- Open-Meteo API 폴백 제거
- DB 저장 시 condition(한글 날씨 상태) 정상 저장
- 캐시 데이터도 KMA로 표시

프론트엔드:
- 데이터 소스를 항상 '🇰🇷 기상청 KMA'로 표시
- Open-Meteo 참조 완전 제거
```

---

## 6. 테스트 및 배포 규칙

### 6.1 필수 테스트 항목
- [ ] 기상청 API 정상 호출 확인
- [ ] DB 데이터 정상 저장 확인
- [ ] 대시보드 UI 렌더링 확인
- [ ] 로그 메시지 표시 확인
- [ ] 폴백 모드 동작 확인

### 6.2 배포 전 체크리스트
- [ ] 모든 커밋 메시지가 규칙 준수
- [ ] README.md 및 CLAUDE.md 최신화
- [ ] 의존성(requirements.txt) 최신화
- [ ] GitHub에 변경사항 Push
- [ ] 로컬 테스트 완료

---

## 7. 트러블슈팅 가이드

### 7.1 기상청 API 오류
**오류**: `"resultCode": "01"`
- 원인: 필수 파라미터 누락
- 해결: `base_date`, `base_time`, `nx`, `ny` 확인

**오류**: API 타임아웃
- 원인: 네트워크 지연 또는 API 서버 다운
- 해결: 캐시 데이터 반환 (FALLBACK_MODE)

### 7.2 DB 오류
**오류**: `UNIQUE constraint failed`
- 원인: 중복 데이터 삽입 시도
- 해결: 타임스탬프 기반 중복 검사 추가

**오류**: `table ... does not exist`
- 원인: DB 초기화 미완료
- 해결: `init_db()` 호출 확인

### 7.3 프론트엔드 오류
**오류**: 데이터가 표시되지 않음
- 원인: API 응답 JSON 구조 불일치
- 해결: Console 확인 후 API 응답 검증

---

## 8. 리뷰 체크리스트

코드 리뷰 시 다음 항목을 반드시 확인:

- [ ] 기상청 API 파싱에 예외 핸들러가 있는가?
- [ ] 주요 기상 지표(T1H, REH, WSD)가 모두 추출되는가?
- [ ] `source` 필드가 "Korea Meteorological Administration (KMA)"로 설정되었는가?
- [ ] DB INSERT 시 prepared statement를 사용하는가?
- [ ] 로그 메시지가 표준 포맷(`[시간] 이모지 메시지`)을 따르는가?
- [ ] API 응답이 표준 JSON 스키마를 따르는가?
- [ ] 에러 처리가 명확한가?
- [ ] 커밋 메시지가 규칙을 따르는가?

---

## 9. 자주 묻는 질문 (FAQ)

**Q: Open-Meteo API를 추가로 사용해야 할까?**
A: 아니오. 기상청 API만 사용하세요. 기상청 실패 시에는 캐시만 반환합니다.

**Q: 날씨 상태를 다른 방식으로 표현할 수 있을까?**
A: 아니오. PTY_CODES 테이블의 값(맑음, 비, 눈 등)을 반드시 사용하세요.

**Q: DB에 저장하지 않고 조회만 할 수 있을까?**
A: `/api/weather` 호출 시 자동 저장이 필수입니다. 저장하지 않으려면 별도 엔드포인트를 만들어야 합니다.

**Q: 로그 형식을 바꿀 수 있을까?**
A: 아니오. `[시간] 이모지 메시지 - 위치` 형식은 고정입니다.

---

## 10. 변경 이력

| 버전 | 날짜 | 변경 사항 |
|------|------|---------|
| v1.0 | 2026-10-13 | 초안 작성 |

---

**마지막 업데이트**: 2026-10-13

문의사항은 프로젝트 GitHub Issues에 등록해주세요.
