import json
import os
from collector import collect_transcripts
from database import upload_to_database
from config import DATA_DIR


def main():
    # data 디렉토리 생성
    # os.makedirs(DATA_DIR, exist_ok=True)

    # # video_ids.json 파일에서 비디오 ID 목록 불러오기
    # try:
    #     with open("../video_ids.json", "r") as f:
    #         video_ids = json.load(f)
    #     print(f"✅ {len(video_ids)}개의 비디오 ID를 불러왔습니다.")
    # except FileNotFoundError:
    #     print("❌ video_ids.json 파일을 찾을 수 없습니다.")
    #     return
    # except json.JSONDecodeError:
    #     print("❌ video_ids.json 파일 형식이 올바르지 않습니다.")
    #     return

    # # 1단계: 자막 수집 및 JSON 저장
    # print("\n📥 1단계: 자막 수집 및 JSON 저장")
    # failed_videos = collect_transcripts(video_ids)

    # # 2단계: JSON 데이터를 DB에 업로드
    # if not failed_videos:
    #     print("\n📤 2단계: JSON 데이터를 DB에 업로드")
    #     upload_to_database()
    # else:
    #     print("\n⚠️ 일부 비디오의 자막 수집에 실패했습니다.")
    #     print("DB 업로드를 진행하시겠습니까? (y/n)")
    #     if input().lower() == "y":
    #         print("\n📤 2단계: JSON 데이터를 DB에 업로드")
    upload_to_database()


if __name__ == "__main__":
    main()
