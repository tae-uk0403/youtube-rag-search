import time
import json
import os
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)
from config import REQUEST_DELAY, TRANSCRIPTS_DIR


def fetch_transcript(video_id, max_retries=8):
    """자막 데이터 가져오기"""
    for attempt in range(max_retries):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, languages=["ko", "en"]
            )
            time.sleep(REQUEST_DELAY)
            return transcript
        except (TranscriptsDisabled, NoTranscriptFound):
            print(f"❌ 자막을 찾을 수 없습니다: {video_id}")
            return None
        except Exception:
            if attempt < max_retries - 1:
                print(f"⚠️ 시도 {attempt + 1}/{max_retries} 실패. 재시도 중...")
                time.sleep(2**attempt)
            else:
                print(f"❌ 최대 재시도 횟수 초과: {video_id}")
                return None
    return None


def save_transcript(video_id, transcript):
    """자막 데이터를 JSON 파일로 저장"""
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
    file_path = os.path.join(TRANSCRIPTS_DIR, f"{video_id}.json")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ 자막 저장 실패 ({video_id}): {str(e)}")
        return False


def load_transcript(video_id):
    """저장된 자막 데이터 불러오기"""
    file_path = os.path.join(TRANSCRIPTS_DIR, f"{video_id}.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"❌ 자막 로드 실패 ({video_id}): {str(e)}")
        return None
