from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from rag import search_similar_sentences
import json
from datetime import datetime
import os
import weaviate
from weaviate.classes.init import Auth
from config import WEAVIATE_URL, WEAVIATE_API_KEY

app = FastAPI(
    title="침착맨 유튜브 대사 검색 API",
    description="침착맨 유튜브 영상의 대사를 검색하는 API 서버",
    version="1.0.0",
)

# Weaviate 클라이언트 싱글톤
_weaviate_client = None


def get_weaviate_client():
    global _weaviate_client
    if _weaviate_client is None:
        _weaviate_client = weaviate.connect_to_weaviate_cloud(
            cluster_url=WEAVIATE_URL,
            auth_credentials=Auth.api_key(api_key=WEAVIATE_API_KEY),
            skip_init_checks=True,
        )
    return _weaviate_client


def close_weaviate_client():
    global _weaviate_client
    if _weaviate_client:
        _weaviate_client.close()
        _weaviate_client = None


# 검색 기록을 저장할 디렉토리 생성
SEARCH_HISTORY_DIR = "search_history"
os.makedirs(SEARCH_HISTORY_DIR, exist_ok=True)


class QueryRequest(BaseModel):
    query: str


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
    """검색 기록을 JSON 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SEARCH_HISTORY_DIR}/search_{timestamp}.json"

    history = {"timestamp": timestamp, "question": question, "results": results}

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return filename


@app.on_event("startup")
def startup_event():
    """앱 시작 시 Weaviate 클라이언트 초기화"""
    get_weaviate_client()


@app.on_event("shutdown")
def shutdown_event():
    """앱 종료 시 Weaviate 클라이언트 종료"""
    close_weaviate_client()


@app.get("/health")
def health_check():
    """API 서버 상태 확인"""
    try:
        client = get_weaviate_client()
        return {"status": "healthy", "weaviate": client.is_ready()}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"서버 상태 확인 중 오류 발생: {str(e)}"
        )


@app.post("/api/search", response_model=SearchResponse)
async def api_search(request: QueryRequest):
    """대사 검색 API 엔드포인트"""
    try:
        # 검색 수행
        results = search_similar_sentences(request.query)

        if not results:
            raise HTTPException(status_code=404, detail="검색 결과가 없습니다.")

        # 검색 결과 저장
        save_search_history(request.query, results)

        # 응답 생성
        response = {
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "question": request.query,
            "results": results,
        }

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}"
        )


@app.get("/")
async def root():
    """API 서버 상태 확인"""
    return {
        "status": "running",
        "message": "침착맨 유튜브 대사 검색 API 서버가 실행 중입니다.",
    }
