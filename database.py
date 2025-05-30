import os
import json
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import DataType, Property, Configure
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_weaviate import WeaviateVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from config import (
    WEAVIATE_URL,
    CLASS_NAME,
    WEAVIATE_API_KEY,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TRANSCRIPTS_DIR,
    DATA_DIR,
)

# 배치 크기 설정
BATCH_SIZE = 100


def load_uploaded_files():
    """업로드된 파일 목록 불러오기"""
    uploaded_file = os.path.join(DATA_DIR, "uploaded_files.json")
    try:
        with open(uploaded_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"files": []}


def save_uploaded_files(uploaded_files):
    """업로드된 파일 목록 저장"""
    uploaded_file = os.path.join(DATA_DIR, "uploaded_files.json")
    with open(uploaded_file, "w") as f:
        json.dump(uploaded_files, f, indent=2)


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

    if not client.collections.exists(CLASS_NAME):
        client.collections.create(
            name=CLASS_NAME,
            properties=[
                Property(name="content", data_type=DataType.TEXT),
                Property(name="channel_id", data_type=DataType.TEXT),
                Property(name="video_id", data_type=DataType.TEXT),
                Property(name="start", data_type=DataType.NUMBER),
                Property(name="end", data_type=DataType.NUMBER),
            ],
            vectorizer_config=Configure.Vectorizer.none(),
        )

    return WeaviateVectorStore(
        client=client,
        index_name=CLASS_NAME,
        text_key="content",
        embedding=embedding,
    )


def convert_segments_to_docs(channel_id, video_id, segments):
    """자막 세그먼트를 문서로 변환"""
    docs = []
    for i in range(0, len(segments), 10):
        group = segments[i : i + 10]
        if not group:
            continue

        combined_text = " ".join(seg["text"] for seg in group)
        doc = Document(
            page_content=combined_text,
            metadata={
                "channel_id": channel_id,
                "video_id": video_id,
                "start": group[0]["start"],
                "end": group[-1]["start"],
            },
        )
        docs.append(doc)
    return docs


def upload_batch(vectorstore, docs_batch):
    """문서 배치 업로드"""
    try:
        vectorstore.add_documents(docs_batch)
        return True
    except Exception as e:
        print(f"❌ 배치 업로드 실패: {str(e)}")
        return False


def upload_to_database():
    """JSON 파일들을 DB에 업로드"""
    client = init_weaviate_client()
    vectorstore = init_vector_store(client)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )

    # 채널 ID 설정
    channel_id = "UCUj6rrhMTR9pipbAWBAMvUQ"

    # 업로드된 파일 목록 불러오기
    uploaded_files = load_uploaded_files()

    # JSON 파일 목록 가져오기 (업로드되지 않은 파일만)
    json_files = [
        f
        for f in os.listdir(TRANSCRIPTS_DIR)
        if f.endswith(".json") and f not in uploaded_files["files"]
    ]

    total_files = len(json_files)
    if total_files == 0:
        print("✅ 모든 파일이 이미 업로드되었습니다.")
        return

    processed_count = 0
    success_count = 0
    failed_count = 0

    print(f"\n📤 총 {total_files}개 파일 업로드 시작")

    for json_file in json_files:
        try:
            video_id = json_file.replace(".json", "")
            file_path = os.path.join(TRANSCRIPTS_DIR, json_file)

            # JSON 파일 읽기
            with open(file_path, "r", encoding="utf-8") as f:
                transcript = json.load(f)

            # 문서 변환
            video_docs = convert_segments_to_docs(channel_id, video_id, transcript)
            if not video_docs:
                print(f"❌ {video_id}: 문서 변환 실패")
                failed_count += 1
                continue

            # 문서 분할
            split_docs = splitter.split_documents(video_docs)

            # 배치 단위로 업로드
            for i in range(0, len(split_docs), BATCH_SIZE):
                batch = split_docs[i : i + BATCH_SIZE]
                if upload_batch(vectorstore, batch):
                    print(f"✅ {video_id}: 배치 업로드 완료 ({len(batch)} 문서)")
                else:
                    print(f"❌ {video_id}: 배치 업로드 실패")
                    failed_count += 1
                    continue

            # 업로드 성공한 파일 기록
            uploaded_files["files"].append(json_file)
            save_uploaded_files(uploaded_files)

            success_count += 1
            print(f"✅ {video_id}: 전체 업로드 완료")

        except Exception as e:
            print(f"❌ {video_id}: 업로드 실패 - {str(e)}")
            failed_count += 1

        processed_count += 1
        print(f"\n📊 진행 상황: {processed_count}/{total_files}")
        print(f"✅ 성공: {success_count}")
        print(f"❌ 실패: {failed_count}")

    client.close()

    print("\n📊 최종 업로드 결과:")
    print(f"✅ 총 처리된 파일: {total_files}")
    print(f"✅ 성공: {success_count}")
    print(f"❌ 실패: {failed_count}")
