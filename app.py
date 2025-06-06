import streamlit as st
import requests
import json
from datetime import datetime
import os

# from config import API_URL  # config에서 API_URL import

# API 서버 URL을 config에서 가져옴
API_URL = "http://203.252.147.202:8200/api/search"  # 이 줄 제거

# 검색 기록을 저장할 디렉토리 생성
SEARCH_HISTORY_DIR = "search_history"
os.makedirs(SEARCH_HISTORY_DIR, exist_ok=True)


def save_search_history(question, results):
    """검색 기록을 JSON 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SEARCH_HISTORY_DIR}/search_{timestamp}.json"

    history = {"timestamp": timestamp, "question": question, "results": results}

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return filename


st.set_page_config(page_title="침착맨 유튜브 대사 검색", page_icon="🔍", layout="wide")

# CSS로 YouTube 영상 크기 조절
st.markdown(
    """
<style>
    .stVideo {
        width: 50%;
        margin: 0 auto;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title("🔍 침착맨 유튜브 대사 검색 시스템")

# 검색 타입 선택
search_type = st.radio(
    "검색 방식 선택",
    ["벡터 검색 (의미 기반)", "BM25 검색 (키워드 기반)"],
    help="벡터 검색은 의미 기반으로, BM25 검색은 키워드 기반으로 검색합니다.",
)

# 검색 가이드라인 수정
st.markdown(
    """
### 검색 가이드라인
- 정확한 대사가 아니어도 괜찮습니다! 떠오르는 대사를 자유롭게 검색해보세요.
- 벡터 검색: 의미적으로 유사한 대사를 찾습니다. 정확한 단어가 아니어도 찾을 수 있습니다.
- BM25 검색: 키워드 기반으로 검색합니다. 정확한 단어가 포함된 대사를 찾습니다.
- 더 자세한 대사를 입력할수록 더 정확한 결과를 찾을 수 있습니다.
- 단어보다 긴 대사를 입력해보세요! 길수록 정확도가 올라갑니다!
- 예시: "다른 사람이 이기는 걸 좋아해 봐.. 그럼 아빠도 행복할걸?"


### 유의사항
- 현재는 침착맨 원본 박물관, 침착맨 플러스는 추후 추가 예정입니다.
- 유튜브의 자동 생성 자막 기반으로 검색을 하기에 정확도가 떨어질 수 있습니다.
- 자막이 없는 경우 검색 결과가 없을 수 있습니다. 재미로 이용해주세요 :)
"""
)

# 예시 검색어와 결과 표시
with st.expander("📺 예시 검색 결과 보기"):
    st.markdown(
        """
    ### 예시 검색어: "다른 사람이 이기는 걸 좋아해 봐.. 그럼 아빠도 행복할걸?"
    """
    )

    # 예시 검색 API 호출
    try:
        response = requests.post(
            API_URL,
            json={"query": "다른 사람이 이기는 걸 좋아해 봐.. 그럼 아빠도 행복할걸?"},
        )

        if response.status_code == 200:
            data = response.json()
            example_results = data["results"]

            # 예시 검색 결과 저장
            save_search_history("예시 검색", example_results)

            for i, result in enumerate(example_results, 1):
                with st.container():
                    st.markdown("---")
                    st.markdown(f"### 결과 {i}")

                    # YouTube 영상 삽입
                    st.video(result["youtube_link"])

                    # 자막 내용과 타임스탬프 링크
                    st.markdown(
                        f"**⏱️ [타임스탬프: {result['start_time']}초]"
                        f"({result['youtube_link']})**"
                    )
                    st.markdown(f"> {result['content']}")
        else:
            st.error("예시 검색 결과를 불러오는데 실패했습니다.")
    except Exception as e:
        st.error(f"예시 검색 중 오류가 발생했습니다: {str(e)}")

st.markdown("---")

# 실제 검색어 입력
question = st.text_input(
    "검색어를 입력하세요",
    placeholder="예: 다른 사람이 이기는 걸 좋아해 봐.. 그럼 아빠도 행복할걸?",
)

if question:
    try:
        # 검색 타입 매핑
        search_type_map = {
            "벡터 검색 (의미 기반)": "vector",
            "BM25 검색 (키워드 기반)": "bm25",
        }

        # API 호출
        response = requests.post(
            API_URL,
            json={"query": question, "search_type": search_type_map[search_type]},
        )

        if response.status_code == 200:
            data = response.json()
            results = data["results"]

            st.success(f"검색 결과: {len(results)}개의 관련 영상을 찾았습니다.")
            st.info(f"사용된 검색 방식: {search_type}")

            # 검색 결과 저장
            saved_file = save_search_history(question, results)
            st.info(f"검색 기록이 저장되었습니다: {saved_file}")

            # 결과 표시
            for i, result in enumerate(results, 1):
                with st.container():
                    st.markdown("---")
                    st.markdown(f"### 결과 {i}")

                    # YouTube 영상 삽입
                    st.video(result["youtube_link"])

                    # 자막 내용과 타임스탬프 링크
                    st.markdown(
                        f"**⏱️ [타임스탬프: {result['start_time']}초]"
                        f"({result['youtube_link']})**"
                    )
                    st.markdown(f"> {result['content']}")
        else:
            st.error(f"검색 실패: {response.json()['detail']}")

    except Exception as e:
        st.error(f"API 요청 중 오류가 발생했습니다: {str(e)}")
