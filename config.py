import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 서버 설정
# API_HOST = os.getenv("API_HOST", "api.search.com")
API_HOST = os.getenv("API_HOST", "203.252.147.202")
API_PORT = os.getenv("API_PORT", "8200")
API_URL = f"http://{API_HOST}:{API_PORT}/api/search"

# Weaviate 설정
WEAVIATE_URL = "http://localhost:8080"  # 로컬 Weaviate 서버 URL
WEAVIATE_API_KEY = None  # 로컬에서는 API 키가 필요 없음
CLASS_NAME = "YoutubeTranscript"

# OpenAI API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# 처리 설정
SEGMENT_SIZE = 10
CHUNK_SIZE = 3000
CHUNK_OVERLAP = 300
MAX_WORKERS = 5
REQUEST_DELAY = 1

# 임베딩 모델 설정
EMBEDDING_MODEL = "dragonkue/BGE-m3-ko"

# 데이터 저장 경로
DATA_DIR = "data"
TRANSCRIPTS_DIR = "data/transcripts"
