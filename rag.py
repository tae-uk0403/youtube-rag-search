import os
import weaviate
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_weaviate import WeaviateVectorStore
from weaviate.classes.query import Filter

from config import (
    WEAVIATE_URL,
    CLASS_NAME,
    WEAVIATE_API_KEY,
    EMBEDDING_MODEL,
)

_executor = ThreadPoolExecutor(max_workers=4)


def init_weaviate_client():
    start_time = time.time()
    try:
        client = weaviate.connect_to_local(
            host="localhost",
            port=8080,
            grpc_port=50051,
            headers={},
        )
        connection_time = time.time() - start_time
        print(f"DB 연결 시간: {connection_time:.2f}초")
        return client
    except Exception as e:
        raise


def init_vector_store(client):
    start_time = time.time()
    embedding = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu", "trust_remote_code": True},
        encode_kwargs={
            "normalize_embeddings": True,
            "padding": True,
            "max_length": 512,
        },
    )

    vectorstore = WeaviateVectorStore(
        client=client,
        index_name=CLASS_NAME,
        text_key="content",
        embedding=embedding,
    )
    init_time = time.time() - start_time
    print(f"벡터 스토어 초기화 시간: {init_time:.2f}초")
    return vectorstore


def get_youtube_link(video_id, start_time):
    return f"https://www.youtube.com/watch?v={video_id}&t={int(start_time)}s"


async def search_similar_sentences(question):
    total_start_time = time.time()

    # DB 연결 시간 측정
    client_start_time = time.time()
    client = init_weaviate_client()
    client_time = time.time() - client_start_time

    # 벡터 스토어 초기화 시간 측정
    store_start_time = time.time()
    vectorstore = init_vector_store(client)
    store_time = time.time() - store_start_time

    try:
        # 검색 시간 측정
        search_start_time = time.time()
        loop = asyncio.get_event_loop()
        docs = await loop.run_in_executor(
            _executor, lambda: vectorstore.similarity_search(question, k=7)
        )
        search_time = time.time() - search_start_time

        # 결과 처리 시간 측정
        process_start_time = time.time()
        results = []
        for doc in docs:
            result = {
                "video_id": doc.metadata["video_id"],
                "start_time": doc.metadata["start"],
                "content": doc.page_content,
                "youtube_link": get_youtube_link(
                    doc.metadata["video_id"], doc.metadata["start"]
                ),
            }
            results.append(result)
        process_time = time.time() - process_start_time

        total_time = time.time() - total_start_time

        # 시간 측정 결과 출력
        print("\n=== 성능 측정 결과 ===")
        print(f"DB 연결 시간: {client_time:.2f}초")
        print(f"벡터 스토어 초기화 시간: {store_time:.2f}초")
        print(f"검색 실행 시간: {search_time:.2f}초")
        print(f"결과 처리 시간: {process_time:.2f}초")
        print(f"총 소요 시간: {total_time:.2f}초")
        print("====================\n")

        return results

    finally:
        client.close()


def search_similar_sentences_bm25(question: str):
    client = init_weaviate_client()
    try:
        collection = client.collections.get("YoutubeTranscript")
        response = collection.query.bm25(
            query=question, query_properties=["content"], limit=7
        )

        results = []
        for obj in response.objects:
            props = obj.properties
            results.append(
                {
                    "video_id": props["video_id"],
                    "start_time": props["start"],
                    "content": props["content"],
                    "youtube_link": get_youtube_link(props["video_id"], props["start"]),
                }
            )

        return results

    finally:
        client.close()


def search_similar_sentences_exact_match(question: str):
    client = init_weaviate_client()
    try:
        search_terms = question.strip().split()
        collection = client.collections.get("YoutubeTranscript")

        # 검색어 각각을 포함하는 조건 생성 (SQL LIKE '%term%')
        filter_conditions = [
            Filter.by_property("content").like(f"%{term}%") for term in search_terms
        ]
        where_clause = Filter.all(*filter_conditions)

        response = collection.query.fetch_objects(
            limit=10,
            return_properties=["video_id", "start", "content"],
            filters=where_clause,
        )

        results = []
        for obj in response.objects:
            props = obj.properties
            results.append(
                {
                    "video_id": props["video_id"],
                    "start_time": props["start"],
                    "content": props["content"],
                    "youtube_link": get_youtube_link(props["video_id"], props["start"]),
                }
            )

        return results

    finally:
        client.close()
