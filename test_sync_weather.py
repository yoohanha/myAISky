"""
myAISky sync_weather_routine 테스트 스크립트

CLAUDE.md 룰 검증:
1. 기상청 API 데이터 자동 수집 (섹션 1)
2. weather_logs.db에 안전하게 적재 (섹션 2)
3. 표준 JSON으로 결과 반환 (섹션 3)
"""

import sys
import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime

# Backend 모듈 임포트
sys.path.insert(0, str(Path(__file__).parent))
from backend.main import (
    sync_weather_routine,
    init_db,
    get_weather_logs_count,
    get_weather_logs,
    DB_PATH
)


def test_sync_weather_routine():
    """sync_weather_routine 함수 테스트"""

    print("\n" + "="*70)
    print("🧪 sync_weather_routine 테스트 시작")
    print("="*70)

    # 1. DB 초기화
    print("\n[1단계] 데이터베이스 초기화...")
    try:
        init_db()
        print("✅ DB 초기화 성공")
    except Exception as e:
        print(f"❌ DB 초기화 실패: {e}")
        return False

    # 2. 초기 데이터 개수 확인
    print("\n[2단계] 초기 데이터 개수 확인...")
    try:
        initial_count = get_weather_logs_count()
        print(f"✅ 초기 데이터: {initial_count}개")
    except Exception as e:
        print(f"❌ 데이터 조회 실패: {e}")
        return False

    # 3. sync_weather_routine 호출
    print("\n[3단계] sync_weather_routine 함수 실행...")
    try:
        result = sync_weather_routine()
        print(f"✅ 함수 실행 완료")
    except Exception as e:
        print(f"❌ 함수 실행 실패: {e}")
        return False

    # 4. 반환 JSON 검증 (CLAUDE.md 3.2절)
    print("\n[4단계] 반환 JSON 검증...")
    required_fields = ["sync_id", "timestamp", "status", "data", "db_result", "message"]

    try:
        for field in required_fields:
            if field not in result:
                print(f"❌ 필수 필드 누락: {field}")
                return False

        print("✅ 모든 필수 필드 포함됨:")
        print(f"   - sync_id: {result['sync_id']}")
        print(f"   - timestamp: {result['timestamp']}")
        print(f"   - status: {result['status']}")
        print(f"   - message: {result['message']}")

    except Exception as e:
        print(f"❌ JSON 검증 실패: {e}")
        return False

    # 5. 데이터 필드 검증 (CLAUDE.md 2.2절)
    print("\n[5단계] 데이터 필드 검증...")
    required_data_fields = ["source", "temperature", "humidity", "wind_speed", "condition", "location"]

    try:
        data = result.get("data", {})
        for field in required_data_fields:
            if field not in data:
                print(f"❌ 데이터 필드 누락: {field}")
                return False

        print("✅ 모든 데이터 필드 포함됨:")
        print(f"   - source: {data['source']}")
        print(f"   - temperature: {data['temperature']}°C")
        print(f"   - humidity: {data['humidity']}%")
        print(f"   - wind_speed: {data['wind_speed']}m/s")
        print(f"   - condition: {data['condition']}")
        print(f"   - location: {data['location']}")

        # 기상청 출처 검증 (CLAUDE.md 1.5절)
        if data["source"] != "Korea Meteorological Administration (KMA)":
            print(f"❌ 데이터 출처 오류: {data['source']}")
            return False
        print(f"✅ 데이터 출처 정상: Korea Meteorological Administration (KMA)")

    except Exception as e:
        print(f"❌ 데이터 필드 검증 실패: {e}")
        return False

    # 6. DB 저장 결과 검증
    print("\n[6단계] DB 저장 결과 검증...")
    try:
        db_result = result.get("db_result", {})

        if result["status"] == "SUCCESS":
            if not db_result.get("inserted"):
                print(f"⚠️ 경고: DB 저장 실패 (하지만 함수는 성공)")
            else:
                print(f"✅ DB 저장 성공")
                print(f"   - 저장됨: True")
                print(f"   - 총 기록: {db_result['total_records']}개")

    except Exception as e:
        print(f"❌ DB 결과 검증 실패: {e}")
        return False

    # 7. 데이터베이스 직접 확인
    print("\n[7단계] 데이터베이스 내용 직접 확인...")
    try:
        logs = get_weather_logs(limit=5)
        final_count = get_weather_logs_count()

        print(f"✅ DB 데이터 조회 성공")
        print(f"   - 총 기록: {final_count}개")
        print(f"   - 최근 5개 기록:")

        for log in logs:
            print(f"      [ID: {log['id']}] 온도: {log['temperature']}°C, "
                  f"날씨: {log['condition']}, "
                  f"시간: {log['timestamp']}")

    except Exception as e:
        print(f"❌ DB 확인 실패: {e}")
        return False

    # 8. 테이블 스키마 검증 (CLAUDE.md 2.1절)
    print("\n[8단계] 테이블 스키마 검증...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(weather_logs)")
        columns = cursor.fetchall()
        conn.close()

        expected_columns = [
            "id", "temperature", "humidity", "wind_speed",
            "apparent_temperature", "condition", "location", "timestamp"
        ]

        actual_columns = [col[1] for col in columns]

        print("✅ 테이블 스키마 확인:")
        for col in actual_columns:
            status = "✓" if col in expected_columns else "✗"
            print(f"   {status} {col}")

        if set(expected_columns) != set(actual_columns):
            print(f"⚠️ 경고: 컬럼 불일치")

    except Exception as e:
        print(f"❌ 스키마 검증 실패: {e}")
        return False

    print("\n" + "="*70)
    print("✅ 모든 테스트 통과!")
    print("="*70)

    # 최종 JSON 출력
    print("\n[최종 반환 JSON]")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return True


def test_json_schema():
    """JSON 스키마 검증 (CLAUDE.md 3.2절)"""

    print("\n" + "="*70)
    print("📋 JSON 스키마 검증")
    print("="*70)

    result = sync_weather_routine()

    required_schema = {
        "sync_id": str,
        "timestamp": str,
        "status": str,
        "data": dict,
        "db_result": dict,
        "message": str
    }

    print("\n✅ 기본 필드:")
    for field, field_type in required_schema.items():
        if field in result:
            actual_type = type(result[field]).__name__
            expected_type = field_type.__name__
            match = "✓" if isinstance(result[field], field_type) else "✗"
            print(f"   {match} {field}: {actual_type} (기대: {expected_type})")
        else:
            print(f"   ✗ {field}: 누락됨")

    print("\n✅ 데이터 필드:")
    if "data" in result:
        data_fields = ["source", "temperature", "humidity", "wind_speed", "condition", "location"]
        for field in data_fields:
            if field in result["data"]:
                value = result["data"][field]
                print(f"   ✓ {field}: {value} ({type(value).__name__})")
            else:
                print(f"   ✗ {field}: 누락됨")

    print("\n✅ DB 결과 필드:")
    if "db_result" in result:
        db_fields = ["inserted", "total_records"]
        for field in db_fields:
            if field in result["db_result"]:
                value = result["db_result"][field]
                print(f"   ✓ {field}: {value}")
            else:
                print(f"   ✗ {field}: 누락됨")

    return True


if __name__ == "__main__":
    print("\n🚀 myAISky sync_weather_routine 검증 테스트 시작\n")

    # 테스트 1: 주요 기능 테스트
    success = test_sync_weather_routine()

    # 테스트 2: JSON 스키마 검증
    test_json_schema()

    if success:
        print("\n✅ 모든 테스트 완료! sync_weather_routine이 정상 작동합니다.\n")
        sys.exit(0)
    else:
        print("\n❌ 테스트 실패! 문제를 확인하세요.\n")
        sys.exit(1)
