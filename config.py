import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 서버 설정
API_HOST = os.getenv("API_HOST", "api.search.com")
API_PORT = os.getenv("API_PORT", "8000")
API_URL = f"http://{API_HOST}:{API_PORT}/api/search"

# Weaviate 설정
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
CLASS_NAME = "YoutubeTranscript"

# OpenAI API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Weaviate 설정
# WEAVIATE_URL = "9ouqyournwnqbwhl1oozq.c0.asia-southeast1.gcp.weaviate.cloud"
# WEAVIATE_API_KEY = "7EIJy2Av3FYXjYzGEixxmYVRzTk34aHtlrbB"

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
