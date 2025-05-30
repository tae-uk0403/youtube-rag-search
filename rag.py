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
    return weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=Auth.api_key(api_key=WEAVIATE_API_KEY),
        skip_init_checks=True,
    )


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
        print(f"❌ 오류 발생: {str(e)}")
        return []
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

        print(f"\n✅ 가장 관련 있는 영상: {get_youtube_link(best_video_id, 0)}")
        print(f"🔍 평균 유사도 점수: {best_score:.4f}")
        print(f"📄 관련 문서 수: {len(video_scores[best_video_id])}")

        # 관련 문장 간단히 보기
        print("\n🧩 관련 자막:")
        for doc, score in docs:
            if doc.metadata["video_id"] == best_video_id:
                print(
                    f"⏱️ {doc.metadata['start']}초 → "
                    f"{doc.page_content}  (유사도: {score:.4f})"
                )

        return best_video_id

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
    finally:
        client.close()


def main():
    """메인 함수"""
    print("🔍 유사 문장 검색 시스템이 준비되었습니다.")
    print("1: 유사 문장 검색")
    print("2: 가장 관련 있는 영상 찾기")
    print("종료하려면 'q' 또는 'quit'를 입력하세요.")

    while True:
        choice = input("\n❓ 기능 선택 (1/2): ").strip()

        if choice.lower() in ["q", "quit"]:
            print("👋 프로그램을 종료합니다.")
            break

        if choice not in ["1", "2"]:
            print("❌ 1 또는 2를 입력해주세요.")
            continue

        question = input("❓ 검색어: ").strip()
        if not question:
            print("❌ 검색어를 입력해주세요.")
            continue

        if choice == "1":
            results = search_similar_sentences(question)
            for result in results:
                print(f"📺 영상: {result['youtube_link']}")
                print(f"⏱️ {result['start_time']}초 → {result['content']}")
        else:
            find_best_video_for_question(question)


if __name__ == "__main__":
    main()
