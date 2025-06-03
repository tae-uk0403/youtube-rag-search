import os

import weaviate
from weaviate.classes.init import Auth
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_weaviate import WeaviateVectorStore
from collections import defaultdict
from config import (
    WEAVIATE_URL,
    CLASS_NAME,
    WEAVIATE_API_KEY,
    EMBEDDING_MODEL,
)


def init_weaviate_client():
    """Weaviate 클라이언트 초기화"""
    try:
        client = weaviate.connect_to_local(
            host="localhost",
            port=8080,
            grpc_port=50051,
            headers={},  # 필요시 헤더 추가
        )
        return client
    except Exception as e:
        raise


def init_vector_store(client):
    """벡터 스토어 초기화"""
    embedding = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu", "trust_remote_code": True},
        encode_kwargs={
            "normalize_embeddings": True,
            "padding": True,
            "max_length": 512,
        },
    )

    return WeaviateVectorStore(
        client=client,
        index_name=CLASS_NAME,
        text_key="content",
        embedding=embedding,
    )


def get_youtube_link(video_id, start_time):
    """YouTube 링크 생성 (타임스탬프 포함)"""
    return f"https://www.youtube.com/watch?v={video_id}&t={int(start_time)}s"


def search_similar_sentences(question):
    """질문과 유사한 문장 검색"""
    client = init_weaviate_client()
    vectorstore = init_vector_store(client)

    try:
        # 유사 문장 검색
        docs = vectorstore.similarity_search(
            question,
            k=7,  # 검색할 문서 수
        )

        # 결과를 딕셔너리 형태로 반환
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

        return results

    except Exception as e:
        return []
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
    """입력된 문장의 모든 단어를 포함한 문장 검색"""
    client = init_weaviate_client()
    try:
        search_terms = question.strip().split()

        collection = client.collections.get("YoutubeTranscript")

        # AND 조건으로 모든 단어 포함 필터 구성
        filter_conditions = [
            {"path": ["content"], "operator": "Contains", "valueText": term}
            for term in search_terms
        ]

        where_clause = {
            "operator": "And",
            "operands": filter_conditions,
        }

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


def find_best_video_for_question(question):
    """질문과 가장 관련 있는 영상 찾기"""
    client = init_weaviate_client()
    vectorstore = init_vector_store(client)

    try:
        docs = vectorstore.similarity_search_with_score(question, k=1000)

        # 📊 video_id → [scores] 로 매핑
        video_scores = defaultdict(list)
        for doc, score in docs:
            video_id = doc.metadata["video_id"]
            video_scores[video_id].append(score)

        # 📈 평균 유사도 기준 정렬 (score가 낮을수록 유사함)
        sorted_videos = sorted(
            video_scores.items(), key=lambda item: sum(item[1]) / len(item[1])
        )

        # 📺 가장 관련 있는 영상
        best_video_id = sorted_videos[0][0]
        best_score = sum(video_scores[best_video_id]) / len(video_scores[best_video_id])

        return best_video_id

    except Exception as e:
        return None
    finally:
        client.close()


def main():
    """메인 함수"""
    while True:
        choice = input("\n기능 선택 (1/2): ").strip()

        if choice.lower() in ["q", "quit"]:
            break

        if choice not in ["1", "2"]:
            continue

        question = input("검색어: ").strip()
        if not question:
            continue

        if choice == "1":
            results = search_similar_sentences(question)
            for result in results:
                print(f"영상: {result['youtube_link']}")
                print(f"{result['start_time']}초 → {result['content']}")
        else:
            find_best_video_for_question(question)


if __name__ == "__main__":
    main()
