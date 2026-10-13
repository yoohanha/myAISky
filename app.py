"""
myAISky - AI Weather & Agent Monitoring Dashboard
FastAPI 백엔드 서버
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import requests
from datetime import datetime
from pathlib import Path

app = FastAPI(title="myAISky", version="1.0.0")

# StaticFiles를 통해 이미지 폴더 마운트
app.mount("/images", StaticFiles(directory="images"), name="images")


def get_weather_data():
    """
    Open-Meteo API를 사용하여 실시간 기상 데이터 조회
    (API 키 불필요, 무료 사용 가능)
    """
    try:
        # 서울 기준 좌표 (latitude=37.5665, longitude=126.9780)
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
        # 폴백 데이터 반환 (개발/테스트용)
        return {
            "location": "Seoul, South Korea",
            "temperature": 18.5,
            "apparent_temperature": 17.2,
            "humidity": 65,
            "wind_speed": 3.5,
            "status": "FALLBACK_MODE",
            "message": "실시간 데이터 로드 불가 - 캐시 데이터 표시"
        }


# 기상 데이터 캐시 (실제 프로덕션에서는 Redis 등 사용)
weather_cache = None
cache_timestamp = None


@app.get("/", response_class=HTMLResponse)
def read_root():
    """
    myAISky 대시보드 메인 페이지
    sky.jpg 배경이미지가 적용된 모던 UI 렌더링
    """
    return """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>myAISky - AI Weather & Agent Monitoring Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background-image: url('/images/sky.jpg');
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
                background-color: #87CEEB;
                min-height: 100vh;
                padding: 20px;
                color: #333;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: rgba(248, 245, 238, 0.95);
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.6);
                padding: 40px;
                backdrop-filter: blur(10px);
            }

            /* 헤더 섹션 */
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 40px;
                border-bottom: 2px solid rgba(100, 180, 220, 0.2);
                padding-bottom: 30px;
            }

            .header-left h1 {
                font-size: 3.5rem;
                color: #2c5aa0;
                font-weight: 700;
                letter-spacing: -1px;
                margin-bottom: 8px;
            }

            .header-left p {
                font-size: 1.1rem;
                color: #666;
                font-weight: 300;
            }

            .status-badge {
                background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                color: white;
                padding: 12px 24px;
                border-radius: 30px;
                font-weight: 600;
                font-size: 0.95rem;
                box-shadow: 0 4px 15px rgba(34, 197, 94, 0.4);
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }

            /* 메인 2분할 레이아웃 */
            .main-content {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-bottom: 30px;
            }

            /* 통계 카드 - 전체 너비 */
            .stats-section {
                grid-column: 1 / -1;
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 20px;
            }

            .stat-card {
                background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
                padding: 25px;
                border-radius: 15px;
                border: 1px solid rgba(100, 180, 220, 0.3);
                text-align: center;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }

            .stat-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
            }

            .stat-card .label {
                font-size: 0.9rem;
                color: #999;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 10px;
            }

            .stat-card .value {
                font-size: 2.5rem;
                font-weight: 700;
                color: #2c5aa0;
                margin-bottom: 5px;
            }

            .stat-card .unit {
                font-size: 0.9rem;
                color: #999;
            }

            /* 좌측: 실시간 기상 데이터 */
            .weather-section {
                background: linear-gradient(135deg, #ffffff 0%, #f5f9fc 100%);
                padding: 30px;
                border-radius: 15px;
                border: 1px solid rgba(100, 180, 220, 0.3);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            }

            .weather-section h2 {
                font-size: 1.5rem;
                color: #2c5aa0;
                margin-bottom: 25px;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .weather-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 0;
                border-bottom: 1px solid rgba(100, 180, 220, 0.2);
            }

            .weather-item:last-child {
                border-bottom: none;
            }

            .weather-item .label {
                font-weight: 600;
                color: #666;
            }

            .weather-item .value {
                font-size: 1.3rem;
                font-weight: 700;
                color: #2c5aa0;
            }

            /* 우측: AI 에이전트 로그 */
            .agent-log-section {
                background: #2a2a3e;
                color: #e0e0e0;
                padding: 30px;
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
                font-family: 'Courier New', monospace;
            }

            .agent-log-section h2 {
                font-size: 1.5rem;
                color: #4ade80;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .log-container {
                background: #1a1a2e;
                padding: 20px;
                border-radius: 10px;
                font-size: 0.9rem;
                max-height: 300px;
                overflow-y: auto;
                line-height: 1.6;
            }

            .log-entry {
                margin-bottom: 10px;
                color: #86efac;
            }

            .log-time {
                color: #64748b;
                margin-right: 10px;
            }

            /* 하단: 수동 제어 패널 */
            .control-panel {
                background: linear-gradient(135deg, #ffffff 0%, #f5f9fc 100%);
                padding: 30px;
                border-radius: 15px;
                border: 1px solid rgba(100, 180, 220, 0.3);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
                margin-top: 30px;
            }

            .control-panel h3 {
                font-size: 1.3rem;
                color: #2c5aa0;
                margin-bottom: 25px;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .control-buttons {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }

            button {
                padding: 14px 28px;
                border: 2px solid #2c5aa0;
                background: #2c5aa0;
                color: white;
                border-radius: 10px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(44, 90, 160, 0.3);
            }

            button:hover {
                background: #1e4175;
                border-color: #1e4175;
                box-shadow: 0 6px 20px rgba(44, 90, 160, 0.4);
                transform: translateY(-2px);
            }

            button:active {
                transform: translateY(0);
            }

            .btn-secondary {
                background: white;
                color: #2c5aa0;
                border-color: #2c5aa0;
            }

            .btn-secondary:hover {
                background: #f5f9fc;
            }

            .btn-success {
                background: #22c55e;
                border-color: #22c55e;
            }

            .btn-success:hover {
                background: #16a34a;
                border-color: #16a34a;
            }

            .status-text {
                margin-top: 20px;
                padding: 15px;
                background: rgba(34, 197, 94, 0.1);
                border-left: 4px solid #22c55e;
                border-radius: 5px;
                color: #166534;
                display: none;
            }

            .status-text.show {
                display: block;
            }

            /* 스크롤바 스타일 */
            .log-container::-webkit-scrollbar {
                width: 8px;
            }

            .log-container::-webkit-scrollbar-track {
                background: #0f0f1e;
            }

            .log-container::-webkit-scrollbar-thumb {
                background: #4a4a6a;
                border-radius: 4px;
            }

            .log-container::-webkit-scrollbar-thumb:hover {
                background: #6a6a8a;
            }

            /* 반응형 디자인 */
            @media (max-width: 1200px) {
                .main-content {
                    grid-template-columns: 1fr;
                }

                .stats-section {
                    grid-template-columns: repeat(2, 1fr);
                }
            }

            @media (max-width: 768px) {
                .container {
                    padding: 20px;
                }

                .header {
                    flex-direction: column;
                    gap: 20px;
                    align-items: flex-start;
                }

                .header-left h1 {
                    font-size: 2.5rem;
                }

                .stats-section {
                    grid-template-columns: repeat(2, 1fr);
                }

                .control-buttons {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- 헤더 -->
            <div class="header">
                <div class="header-left">
                    <h1>myAISky</h1>
                    <p>🌤️ AI Weather & Agent Monitoring Dashboard</p>
                </div>
                <div class="status-badge">🟢 24/7 Sandbox Active</div>
            </div>

            <!-- 메인 콘텐츠 -->
            <div class="main-content">
                <!-- 통계 카드 -->
                <div class="stats-section">
                    <div class="stat-card">
                        <div class="label">온도</div>
                        <div class="value" id="temp">--</div>
                        <div class="unit">°C</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">습도</div>
                        <div class="value" id="humidity">--</div>
                        <div class="unit">%</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">풍속</div>
                        <div class="value" id="wind">--</div>
                        <div class="unit">km/h</div>
                    </div>
                    <div class="stat-card">
                        <div class="label">체감온도</div>
                        <div class="value" id="apparent">--</div>
                        <div class="unit">°C</div>
                    </div>
                </div>

                <!-- 좌측: 실시간 기상 데이터 -->
                <div class="weather-section">
                    <h2>🌍 실시간 기상 데이터 분석</h2>
                    <div class="weather-item">
                        <span class="label">위치</span>
                        <span class="value" id="location">Seoul, South Korea</span>
                    </div>
                    <div class="weather-item">
                        <span class="label">현재 온도</span>
                        <span class="value" id="weather-temp">로드 중...</span>
                    </div>
                    <div class="weather-item">
                        <span class="label">체감 온도</span>
                        <span class="value" id="weather-apparent">로드 중...</span>
                    </div>
                    <div class="weather-item">
                        <span class="label">습도</span>
                        <span class="value" id="weather-humidity">로드 중...</span>
                    </div>
                    <div class="weather-item">
                        <span class="label">풍속</span>
                        <span class="value" id="weather-wind">로드 중...</span>
                    </div>
                    <div class="weather-item">
                        <span class="label">마지막 업데이트</span>
                        <span class="value" id="last-update" style="font-size: 0.9rem;">--:--</span>
                    </div>
                </div>

                <!-- 우측: AI 에이전트 실시간 로그 -->
                <div class="agent-log-section">
                    <h2>⚙️ AI 에이전트 실시간 로그</h2>
                    <div class="log-container" id="log-container">
                        <div class="log-entry">
                            <span class="log-time">[2026-10-13 18:00:00]</span>
                            System initialized - myAISky Dashboard v1.0.0
                        </div>
                        <div class="log-entry">
                            <span class="log-time">[2026-10-13 18:00:01]</span>
                            Weather data service connected - API ready
                        </div>
                        <div class="log-entry">
                            <span class="log-time">[2026-10-13 18:00:02]</span>
                            Agent monitoring system active - 24/7 sandbox mode
                        </div>
                        <div class="log-entry">
                            <span class="log-time">[2026-10-13 18:00:03]</span>
                            Dashboard UI rendering complete - Ready for user interaction
                        </div>
                    </div>
                </div>
            </div>

            <!-- 하단: 수동 제어 패널 -->
            <div class="control-panel">
                <h3>🎮 Manual Control Panel</h3>
                <div class="control-buttons">
                    <button class="btn-success" onclick="fetchWeather()">
                        🔄 기상 데이터 동기화
                    </button>
                    <button class="btn-secondary" onclick="generateReport()">
                        📊 리포트 생성
                    </button>
                    <button class="btn-secondary" onclick="refreshDashboard()">
                        🔁 대시보드 새로고침
                    </button>
                    <button class="btn-secondary" onclick="exportData()">
                        💾 데이터 내보내기
                    </button>
                </div>
                <div class="status-text" id="status-message"></div>
            </div>
        </div>

        <script>
            // 초기 로드 시 기상 데이터 가져오기
            document.addEventListener('DOMContentLoaded', () => {
                fetchWeather();
                // 10분마다 자동 갱신
                setInterval(fetchWeather, 600000);
            });

            // 기상 데이터 가져오기
            async function fetchWeather() {
                try {
                    const response = await fetch('/api/weather');
                    const data = await response.json();

                    if (data.status === 'OK' || data.status === 'FALLBACK_MODE') {
                        // 통계 카드 업데이트
                        document.getElementById('temp').textContent = data.temperature.toFixed(1);
                        document.getElementById('humidity').textContent = data.humidity;
                        document.getElementById('wind').textContent = data.wind_speed.toFixed(1);
                        document.getElementById('apparent').textContent = data.apparent_temperature.toFixed(1);

                        // 기상 데이터 섹션 업데이트
                        document.getElementById('weather-temp').textContent = data.temperature.toFixed(1) + '°C';
                        document.getElementById('weather-apparent').textContent = data.apparent_temperature.toFixed(1) + '°C';
                        document.getElementById('weather-humidity').textContent = data.humidity + '%';
                        document.getElementById('weather-wind').textContent = data.wind_speed.toFixed(1) + ' km/h';

                        // 시간 업데이트
                        const now = new Date();
                        document.getElementById('last-update').textContent =
                            now.toLocaleTimeString('ko-KR', { hour12: false });

                        // 로그 추가
                        addLog('기상 데이터 동기화 완료 - ' + data.location);
                        if (data.status === 'FALLBACK_MODE') {
                            addLog('⚠️ API 연결 오류 - 캐시 데이터 사용 중');
                        }
                    }
                } catch (error) {
                    console.error('오류:', error);
                    addLog('❌ 기상 데이터 로드 실패');
                }
            }

            // 로그 추가 함수
            function addLog(message) {
                const container = document.getElementById('log-container');
                const time = new Date().toLocaleTimeString('ko-KR', { hour12: false });
                const entry = document.createElement('div');
                entry.className = 'log-entry';
                entry.innerHTML = `<span class="log-time">[${time}]</span> ${message}`;
                container.appendChild(entry);
                container.scrollTop = container.scrollHeight;
            }

            // 리포트 생성
            function generateReport() {
                const timestamp = new Date().toLocaleString('ko-KR');
                const temp = document.getElementById('temp').textContent;
                const humidity = document.getElementById('humidity').textContent;
                const wind = document.getElementById('wind').textContent;

                const report = `
                ===== myAISky Weather Report =====
                Generated: ${timestamp}

                Temperature: ${temp}°C
                Humidity: ${humidity}%
                Wind Speed: ${wind} km/h

                Report Status: Generated Successfully
                ===================================
                `;

                alert(report);
                addLog('📋 리포트 생성 완료');
                showStatus('리포트가 생성되었습니다.');
            }

            // 대시보드 새로고침
            function refreshDashboard() {
                location.reload();
            }

            // 데이터 내보내기
            function exportData() {
                const data = {
                    timestamp: new Date().toISOString(),
                    temperature: document.getElementById('temp').textContent,
                    humidity: document.getElementById('humidity').textContent,
                    windSpeed: document.getElementById('wind').textContent,
                    apparentTemperature: document.getElementById('apparent').textContent
                };

                const json = JSON.stringify(data, null, 2);
                const blob = new Blob([json], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `weather-data-${new Date().getTime()}.json`;
                link.click();

                addLog('💾 데이터 내보내기 완료');
                showStatus('데이터가 JSON 파일로 내보내졌습니다.');
            }

            // 상태 메시지 표시
            function showStatus(message) {
                const statusElement = document.getElementById('status-message');
                statusElement.textContent = '✅ ' + message;
                statusElement.classList.add('show');
                setTimeout(() => statusElement.classList.remove('show'), 3000);
            }
        </script>
    </body>
    </html>
    """


@app.get("/api/weather")
def get_weather():
    """
    기상 데이터를 JSON 형식으로 반환하는 API 엔드포인트
    """
    global weather_cache, cache_timestamp

    # 캐시 검증 (실제로는 더 정교한 캐싱 로직 필요)
    if weather_cache is None:
        weather_cache = get_weather_data()
        cache_timestamp = datetime.now()

    return weather_cache


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║           myAISky - AI Weather & Agent Monitoring             ║
    ║                    FastAPI Backend Server                     ║
    ╚════════════════════════════════════════════════════════════════╝

    📊 대시보드 주소: http://localhost:8000
    🌤️  기상 API 주소: http://localhost:8000/api/weather

    ▶️  서버 실행 명령어:
       uvicorn app:app --reload --host 0.0.0.0 --port 8000

    💡 개발 모드에서는 --reload 옵션으로 자동 재시작됩니다.

    🔗 브라우저에서 http://localhost:8000 으로 접속하세요.

    ╔════════════════════════════════════════════════════════════════╗
    """)

    # Uvicorn 서버 실행
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
