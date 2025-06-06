import requests
import time
import concurrent.futures
import statistics
from datetime import datetime
import json
import os
from config import API_URL  # API_URL을 config에서 import

# API 서버 URL을 config에서 가져옴
API_URL = "http://203.252.147.202:8200/api/search"

# 테스트 결과를 저장할 디렉토리
TEST_RESULTS_DIR = "test_results"
os.makedirs(TEST_RESULTS_DIR, exist_ok=True)

# 테스트할 검색어 목록
TEST_QUERIES = [
    "다른 사람이 이기는 걸 좋아해 봐.. 그럼 아빠도 행복할걸?",
    "이거 진짜 웃기네",
    "아 진짜 화나네",
    "이게 뭐야",
    "와 진짜 대박이다",
    "이거 어떻게 하는 거야",
    "아 진짜 어렵다",
    "이거 진짜 재미있다",
    "와 진짜 신기하다",
    "이거 진짜 좋다",
]

# 검색 타입 목록 (현재 구현된 타입만 포함)
SEARCH_TYPES = [
    "exact_match",
    "vector",
    "vector_no_celery",
]  # Celery 사용 여부 비교를 위한 타입 추가


def check_api_health():
    """API 서버 상태 확인"""
    try:
        response = requests.get("http://203.252.147.202:8200/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"API 서버 응답 시간: {response.elapsed.total_seconds():.2f}초")
            return True
        else:
            print(f"API 서버 응답 오류 (상태 코드: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("API 서버에 연결할 수 없습니다.")
        return False
    except requests.exceptions.Timeout:
        print("API 서버 응답 시간 초과")
        return False
    except Exception as e:
        print(f"예상치 못한 오류: {str(e)}")
        return False


def make_search_request(query, search_type="vector"):
    """단일 검색 요청 수행 및 시간 측정"""
    start_time = time.time()
    try:
        # 1. API 서버 연결 시도
        connection_start = time.time()

        # Celery 사용 여부에 따라 다른 엔드포인트 사용
        if search_type == "vector_no_celery":
            url = "http://203.252.147.202:8200/api/search_no_celery"
        else:
            url = API_URL

        response = requests.post(
            url, json={"query": query, "search_type": search_type}, timeout=60
        )
        connection_time = time.time() - connection_start

        end_time = time.time()
        processing_time = end_time - start_time

        # 응답 내용 파싱
        response_data = response.json() if response.status_code == 200 else None

        if response.status_code == 200:
            print(
                f"검색 완료 - 소요시간: {processing_time:.2f}초 (연결: {connection_time:.2f}초)"
            )

        return {
            "query": query,
            "search_type": search_type,
            "status_code": response.status_code,
            "processing_time": processing_time,
            "connection_time": connection_time,
            "success": response.status_code == 200,
            "error": None if response.status_code == 200 else response.text,
            "response_data": response_data,
            "error_type": (
                "connection_error"
                if "Connection" in str(response.text)
                else "server_error"
            ),
        }
    except requests.exceptions.Timeout:
        end_time = time.time()
        print(f"요청 시간 초과 - 소요시간: {end_time - start_time:.2f}초")
        return {
            "query": query,
            "search_type": search_type,
            "status_code": None,
            "processing_time": end_time - start_time,
            "connection_time": end_time - start_time,
            "success": False,
            "error": "요청 시간 초과",
            "error_type": "timeout_error",
        }
    except requests.exceptions.ConnectionError as e:
        end_time = time.time()
        print(f"연결 오류 - 소요시간: {end_time - start_time:.2f}초")
        return {
            "query": query,
            "search_type": search_type,
            "status_code": None,
            "processing_time": end_time - start_time,
            "connection_time": end_time - start_time,
            "success": False,
            "error": str(e),
            "error_type": "connection_error",
        }
    except Exception as e:
        end_time = time.time()
        print(f"예상치 못한 오류 - 소요시간: {end_time - start_time:.2f}초")
        return {
            "query": query,
            "search_type": search_type,
            "status_code": None,
            "processing_time": end_time - start_time,
            "connection_time": end_time - start_time,
            "success": False,
            "error": str(e),
            "error_type": "unknown_error",
        }


def run_concurrent_test(num_users, num_requests_per_user):
    """동시 사용자 테스트 실행"""
    print(f"\n테스트 시작: {num_users}명의 사용자, 각 {num_requests_per_user}개 요청")

    all_results = []
    start_time = time.time()

    # ThreadPoolExecutor를 사용하여 동시 요청 처리
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = []
        for user_id in range(num_users):
            for query_idx, query in enumerate(TEST_QUERIES[:num_requests_per_user], 1):
                for search_type in SEARCH_TYPES:
                    futures.append(
                        executor.submit(make_search_request, query, search_type)
                    )

        # 결과 수집
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                all_results.append(result)
            except Exception as e:
                print(f"요청 처리 중 오류 발생: {str(e)}")

    end_time = time.time()
    total_time = end_time - start_time
    print(f"테스트 완료 - 총 소요시간: {total_time:.2f}초")

    # 결과 분석
    successful_requests = [r for r in all_results if r["success"]]
    failed_requests = [r for r in all_results if not r["success"]]

    # 검색 타입별 성공률 계산
    search_type_stats = {}
    for search_type in SEARCH_TYPES:
        type_requests = [r for r in all_results if r["search_type"] == search_type]
        type_success = [r for r in type_requests if r["success"]]
        search_type_stats[search_type] = {
            "total": len(type_requests),
            "success": len(type_success),
            "success_rate": (
                len(type_success) / len(type_requests) if type_requests else 0
            ),
            "avg_processing_time": (
                statistics.mean([r["processing_time"] for r in type_success])
                if type_success
                else 0
            ),
        }

    # 에러 타입별 분석
    error_types = {}
    for failed in failed_requests:
        error_type = failed.get("error_type", "unknown")
        error_types[error_type] = error_types.get(error_type, 0) + 1

    # 통계 계산
    stats = {
        "total_requests": len(all_results),
        "successful_requests": len(successful_requests),
        "failed_requests": len(failed_requests),
        "total_time": total_time,
        "avg_processing_time": (
            statistics.mean([r["processing_time"] for r in successful_requests])
            if successful_requests
            else 0
        ),
        "avg_connection_time": statistics.mean(
            [r["connection_time"] for r in all_results]
        ),
        "error_types": error_types,
        "search_type_stats": search_type_stats,
        "requests_per_second": (len(all_results) / total_time if total_time > 0 else 0),
    }

    # 결과 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"{TEST_RESULTS_DIR}/test_results_{timestamp}.json"

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "test_config": {
                    "num_users": num_users,
                    "num_requests_per_user": num_requests_per_user,
                },
                "statistics": stats,
                "detailed_results": all_results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    # 결과 출력
    print("\n📊 테스트 결과:")
    print(f"총 요청 수: {stats['total_requests']}")
    print(f"성공한 요청: {stats['successful_requests']}")
    print(f"실패한 요청: {stats['failed_requests']}")
    print(f"총 소요 시간: {stats['total_time']:.2f}초")
    print(f"평균 처리 시간: {stats['avg_processing_time']:.2f}초")
    print(f"평균 연결 시간: {stats['avg_connection_time']:.2f}초")
    print(f"초당 처리 요청 수: {stats['requests_per_second']:.2f}")

    print("\n🔍 검색 타입별 성능:")
    for search_type, type_stats in search_type_stats.items():
        print(f"\n{search_type} 검색:")
        print(f"  총 요청: {type_stats['total']}")
        print(f"  성공: {type_stats['success']}")
        print(f"  성공률: {type_stats['success_rate']*100:.1f}%")
        print(f"  평균 처리 시간: {type_stats['avg_processing_time']:.2f}초")

    print("\n❌ 에러 타입별 분석:")
    for error_type, count in stats["error_types"].items():
        print(f"{error_type}: {count}건")

    # 실패한 요청 상세 정보 출력
    if failed_requests:
        print("\n❌ 실패한 요청 상세 정보:")
        for i, failed in enumerate(failed_requests, 1):
            print(f"\n실패 #{i}")
            print(f"검색어: {failed['query']}")
            print(f"검색 타입: {failed['search_type']}")
            print(f"상태 코드: {failed['status_code']}")
            print(f"처리 시간: {failed['processing_time']:.2f}초")
            print(f"연결 시간: {failed['connection_time']:.2f}초")
            print(f"에러 타입: {failed.get('error_type', 'unknown')}")
            print(f"에러 메시지: {failed['error']}")

    print(f"\n상세 결과가 저장되었습니다: {result_file}")

    return stats


def main():
    # API 서버 상태 확인
    if not check_api_health():
        print("\n⚠️ API 서버가 정상적으로 동작하지 않습니다. 테스트를 중단합니다.")
        return

    # 다양한 사용자 수와 요청 수로 테스트
    test_scenarios = [
        (10, 1),  # 10명이 각각 1개 요청
    ]

    print("\n🚀 성능 테스트 시작")

    for num_users, num_requests in test_scenarios:
        print(f"\n{'='*50}")
        print(f"테스트 시나리오: {num_users}명의 사용자, 각 {num_requests}개 요청")
        print(f"{'='*50}")

        run_concurrent_test(num_users, num_requests)

        # 각 시나리오 사이에 잠시 대기
        time.sleep(10)  # 대기 시간 증가


if __name__ == "__main__":
    main()
