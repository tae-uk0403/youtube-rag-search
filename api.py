from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from rag import (
    search_similar_sentences,
    search_similar_sentences_bm25,
)

from tasks import search_task_vector
from fastapi import BackgroundTasks


import json
from datetime import datetime
import os
import weaviate
import asyncio
import time

app = FastAPI(
    title="침착맨 유튜브 대사 검색 API",
    description="침착맨 유튜브 영상의 대사를 검색하는 API 서버",
    version="1.0.0",
)

_weaviate_client = None


def get_weaviate_client():
    global _weaviate_client
    if _weaviate_client is None:
        _weaviate_client = weaviate.connect_to_local(
            host="127.0.0.1",
            port=8080,
            grpc_port=50051,
            skip_init_checks=True,
        )
    return _weaviate_client


def close_weaviate_client():
    global _weaviate_client
    if _weaviate_client:
        _weaviate_client.close()
        _weaviate_client = None


SEARCH_HISTORY_DIR = "search_history"
os.makedirs(SEARCH_HISTORY_DIR, exist_ok=True)


class QueryRequest(BaseModel):
    query: str
    search_type: str = "vector"


class SearchResult(BaseModel):
    video_id: str
    start_time: float
    content: str
    youtube_link: str


class SearchResponse(BaseModel):
    timestamp: str
    question: str
    results: List[SearchResult]


def save_search_history(question: str, results: List[Dict[str, Any]]) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SEARCH_HISTORY_DIR}/search_{timestamp}.json"

    history = {"timestamp": timestamp, "question": question, "results": results}

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return filename


@app.on_event("startup")
def startup_event():
    get_weaviate_client()


@app.on_event("shutdown")
def shutdown_event():
    close_weaviate_client()


@app.get("/health")
def health_check():
    try:
        client = get_weaviate_client()
        return {"status": "healthy", "weaviate": client.is_ready()}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"서버 상태 확인 중 오류 발생: {str(e)}"
        )


@app.post("/api/search", response_model=SearchResponse)
async def api_search(request: QueryRequest):
    total_start_time = time.time()
    try:
        if request.search_type == "bm25":
            search_start_time = time.time()
            results = search_similar_sentences_bm25(request.query)
            search_time = time.time() - search_start_time
            print(f"BM25 검색 시간: {search_time:.2f}초")
        else:
            # 벡터 검색은 Celery 태스크로 처리
            task_start_time = time.time()
            task = search_task_vector.delay(request.query)
            # 최대 50초 정도 기다림
            results = task.get(timeout=50)
            task_time = time.time() - task_start_time
            print(f"Celery 태스크 처리 시간: {task_time:.2f}초")

            if isinstance(results, dict) and results.get("error"):
                raise HTTPException(status_code=500, detail=results["error"])

        if not results:
            raise HTTPException(status_code=404, detail="검색 결과가 없습니다.")

        # 검색 결과 저장
        save_start_time = time.time()
        save_search_history(request.query, results)
        save_time = time.time() - save_start_time
        print(f"검색 결과 저장 시간: {save_time:.2f}초")

        total_time = time.time() - total_start_time
        print(f"\n=== API 엔드포인트 총 소요 시간: {total_time:.2f}초 ===\n")

        return {
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "question": request.query,
            "results": results,
        }

    except Exception as e:
        total_time = time.time() - total_start_time
        print(
            f"\n=== API 엔드포인트 오류 발생 - 총 소요 시간: {total_time:.2f}초 ===\n"
        )
        raise HTTPException(
            status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/search_no_celery", response_model=SearchResponse)
async def api_search_no_celery(request: QueryRequest):
    total_start_time = time.time()
    try:
        if request.search_type == "vector_no_celery":
            # 벡터 검색을 직접 실행 (Celery 없이)
            search_start_time = time.time()
            results = await search_similar_sentences(request.query)
            search_time = time.time() - search_start_time
            print(f"벡터 검색 시간 (Celery 없음): {search_time:.2f}초")
        else:
            raise HTTPException(status_code=400, detail="잘못된 검색 타입입니다.")

        if not results:
            raise HTTPException(status_code=404, detail="검색 결과가 없습니다.")

        # 검색 결과 저장
        save_start_time = time.time()
        save_search_history(request.query, results)
        save_time = time.time() - save_start_time
        print(f"검색 결과 저장 시간: {save_time:.2f}초")

        total_time = time.time() - total_start_time
        print(
            f"\n=== API 엔드포인트 총 소요 시간 (Celery 없음): {total_time:.2f}초 ===\n"
        )

        return {
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "question": request.query,
            "results": results,
        }

    except Exception as e:
        total_time = time.time() - total_start_time
        print(
            f"\n=== API 엔드포인트 오류 발생 - 총 소요 시간: {total_time:.2f}초 ===\n"
        )
        raise HTTPException(
            status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}"
        )


@app.get("/")
async def root():
    return {
        "status": "running",
        "message": "침착맨 유튜브 대사 검색 API 서버가 실행 중입니다.",
    }
