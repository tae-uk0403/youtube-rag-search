import time
import json
import threading
from queue import Queue
from transcript import fetch_transcript, save_transcript
from config import REQUEST_DELAY, DATA_DIR
import os


def load_processed_ids():
    """처리된 비디오 ID 목록 불러오기"""
    processed_file = os.path.join(DATA_DIR, "processed_videos.json")
    try:
        with open(processed_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"success": [], "failed": []}


def save_processed_ids(processed_ids):
    """처리된 비디오 ID 목록 저장"""
    processed_file = os.path.join(DATA_DIR, "processed_videos.json")
    with open(processed_file, "w") as f:
        json.dump(processed_ids, f, indent=2)


def process_video(video_id, result_queue):
    """단일 비디오 처리"""
    try:
        # 자막 데이터 가져오기
        transcript = fetch_transcript(video_id)
        if not transcript:
            result_queue.put(("failed", video_id))
            return

        # JSON 파일로 저장
        if save_transcript(video_id, transcript):
            result_queue.put(("success", video_id))
        else:
            result_queue.put(("failed", video_id))

    except Exception as e:
        print(f"❌ {video_id}: 오류 발생 - {str(e)}")
        result_queue.put(("failed", video_id))


def worker(video_queue, result_queue):
    """작업자 스레드"""
    while True:
        try:
            video_id = video_queue.get_nowait()
            process_video(video_id, result_queue)
            video_queue.task_done()
            time.sleep(REQUEST_DELAY)
        except Queue.Empty:
            break


def collect_transcripts(video_ids, num_threads=5):
    """자막 수집 및 저장"""
    # 이미 처리된 비디오 ID 불러오기
    processed_ids = load_processed_ids()

    # 처리되지 않은 비디오 ID만 필터링
    new_video_ids = [
        vid
        for vid in video_ids
        if vid not in processed_ids["success"] and vid not in processed_ids["failed"]
    ]

    if not new_video_ids:
        print("✅ 모든 비디오가 이미 처리되었습니다.")
        return []

    total_videos = len(new_video_ids)
    processed_count = 0
    success_count = 0
    failed_count = 0
    failed_videos = []

    print(f"\n📊 수집 시작: 총 {total_videos}개 비디오")

    # 작업 큐와 결과 큐 생성
    video_queue = Queue()
    result_queue = Queue()

    # 작업 큐에 비디오 ID 추가
    for video_id in new_video_ids:
        video_queue.put(video_id)

    # 작업자 스레드 생성 및 시작
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker, args=(video_queue, result_queue))
        t.start()
        threads.append(t)

    # 결과 처리
    while processed_count < total_videos:
        status, video_id = result_queue.get()
        processed_count += 1

        if status == "success":
            success_count += 1
            processed_ids["success"].append(video_id)
        else:
            failed_count += 1
            failed_videos.append(video_id)
            processed_ids["failed"].append(video_id)

        # 진행 상황 출력
        print(f"\n📊 진행 상황: {processed_count}")
        print(f"✅ 성공: {success_count}")
        print(f"❌ 실패: {failed_count}")

        # 처리된 ID 목록 저장
        save_processed_ids(processed_ids)

    # 모든 스레드가 종료될 때까지 대기
    for t in threads:
        t.join()

    # 최종 결과 출력
    print("\n📊 최종 처리 결과:")
    print(f"✅ 총 처리된 비디오: {total_videos}")
    print(f"✅ 성공: {success_count}")
    print(f"❌ 실패: {failed_count}")
    if failed_videos:
        print("\n❌ 실패한 비디오:")
        for vid in failed_videos:
            print(f"- {vid}")

    return failed_videos
