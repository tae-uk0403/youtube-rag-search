# tasks.py
from celery import Celery
from rag import search_similar_sentences
import asyncio

# Celery 기본 설정
celery = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)


# 비동기 함수 실행 헬퍼
def run_async(func, *args):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return asyncio.run(func(*args))
    else:
        return asyncio.run(func(*args))


# 워커 기본 안정성 설정 포함 태스크
@celery.task(
    bind=True,
    max_retries=3,  # 최대 3회 재시도
    default_retry_delay=5,  # 5초 간격으로 재시도
    task_time_limit=60,  # 강제 종료 시간 (초)
    acks_late=True,  # 작업 완료 후 ack (워커 중단 시 자동 재시도됨)
)
def search_task_vector(self, question: str):
    try:
        return run_async(search_similar_sentences, question)
    except Exception as e:
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {"error": f"최대 재시도 초과: {str(e)}"}
