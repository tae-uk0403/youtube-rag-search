# 침착맨 유튜브 대사 검색 시스템

침착맨의 유튜브 영상에서 원하는 대사를 검색할 수 있는 웹 애플리케이션입니다.

## 기능

- 유튜브 영상 대사 검색
- 검색 결과에 해당하는 영상 타임스탬프 제공
- 검색 기록 저장

## 설치 및 실행

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
```bash
export API_URL="http://your-api-server:8000/api/search"
```

3. Streamlit 앱 실행:
```bash
streamlit run app.py
```

## 환경 변수

- `API_URL`: 검색 API 서버 주소

## 기술 스택

- Frontend: Streamlit
- Backend: FastAPI
- Database: Weaviate 