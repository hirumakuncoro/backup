import json
import os
import subprocess
import sys
import unicodedata
from pathlib import Path

import requests

START_INDEX = 1

COURSE_IDS = [
    10262, 10349, 10372, 10385, 10400, 10411, 10428, 10437, 10454, 10467,
    10514, 10955, 11421, 12702, 12811, 13657, 15260, 15514, 16619, 18722,
    19177, 19581, 20770, 21419, 25035, 25128, 25154, 29926, 29928, 29944,
    30620, 31021, 31092, 31106, 31111, 31113, 31150, 31153, 31156, 31158,
    31162, 31164, 31166, 31184, 31188, 31192, 33233, 33421, 34403, 34830,
    35229, 35247, 35269, 35284, 35317, 35319, 35348, 35419, 35573, 35584,
    35731, 35736, 35756, 35765, 35772, 35778, 35785, 35796, 35826, 35851,
    35979, 35987, 35993, 35999, 36446, 36449, 36452, 36856, 37460, 38605,
    41593, 41597, 42248, 42902, 43094, 43867, 43874, 45125, 45129, 45959,
    46708, 46869, 47746, 49092, 49470, 49472, 49678, 49781, 50423, 51241,
    52023, 52564, 53270, 53531, 54036, 54738, 55439, 55977, 57569, 58945,
    60043, 60567, 60683, 61390, 61711, 62426, 66007, 67525, 69718, 69761,
    70149, 70332, 70825, 71239, 71343, 71955, 72277, 72724, 73365, 73829,
    73951, 74856, 75347, 77898, 79581, 80043, 80284, 82051, 82611, 83122,
    83347, 83751, 84840, 87202, 88946, 88951, 88953, 88956,
]

API_TOKEN = os.environ.get("TOKEN", "")
TARGET_DOMAIN = os.environ.get("DOMAIN", "")
# Root folder di Google Drive yang berisi folder "NN - Judul Course"
RCLONE_REMOTE = os.environ.get("REMOTE", "gdrive:AkademiCrypto")


def norm(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def sanitize(name: str) -> str:
    for ch in r'/\:*?"<>|':
        name = name.replace(ch, "_")
    return name.strip()


def list_remote(remote: str) -> dict[str, int]:
    """Return {relative_path: size} untuk semua file di remote (rekursif)."""
    print(f"Listing {remote} via rclone ...")
    try:
        out = subprocess.run(
            ["rclone", "lsjson", "-R", "--files-only", "--no-modtime", "--no-mimetype", remote],
            capture_output=True, text=True, check=True,
        ).stdout
    except FileNotFoundError:
        print("Error: rclone tidak ditemukan di PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error rclone:\n{e.stderr}")
        sys.exit(1)

    files = {}
    for item in json.loads(out):
        files[norm(item["Path"])] = item.get("Size", 0)
    print(f"Ditemukan {len(files)} file di remote.\n")
    return files


def fetch_course(course_id: str) -> dict:
    url = f"https://{TARGET_DOMAIN}/api/v1/courses/{course_id}/modules"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "*/*",
        "Referer": f"https://{TARGET_DOMAIN}/academy/course/{course_id}",
        "x-client-type": "web",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
    }
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != 200:
        return {}
    return r.json().get("data", {}).get("course_modules", {})


def extract_videos(course: dict) -> list[tuple[str, str]]:
    videos = []
    for section in course.get("sections", []):
        section_title = section.get("section_title", section.get("title", "Unknown Section"))
        for lesson in section.get("lessons", []):
            url = lesson.get("video_url", "")
            if url and "mediadelivery.net/embed/" in url:
                lesson_title = lesson.get("lesson_title", lesson.get("title", "Unknown Lesson"))
                videos.append((section_title, lesson_title))
    return videos


def main():
    if not API_TOKEN or not TARGET_DOMAIN:
        print("Error: TOKEN dan DOMAIN harus diset di environment variables.")
        sys.exit(1)

    remote_files = list_remote(RCLONE_REMOTE)
    total_missing = 0
    total_found = 0

    print("=== MULAI VERIFIKASI (Google Drive) ===")

    for idx, cid in enumerate(COURSE_IDS, START_INDEX):
        course = fetch_course(str(cid))
        if not course:
            print(f"[!] Course {cid}: Gagal fetch data API.")
            continue

        raw_title = sanitize(course.get("course_title", f"Course_{cid}"))
        course_title = f"{idx:02d} - {raw_title}"
        videos = extract_videos(course)

        missing = []
        for v_idx, (section_title, lesson_title) in enumerate(videos, 1):
            filename = f"{v_idx:02d} - {sanitize(lesson_title)}.mp4"
            rel = norm(str(Path(course_title) / sanitize(section_title) / filename))

            if remote_files.get(rel, 0) > 0:
                total_found += 1
            else:
                missing.append(rel)

        if not missing:
            print(f"✓ Course {cid} ({course_title}): Lengkap ({len(videos)}/{len(videos)} video).")
        else:
            print(f"✗ Course {cid} ({course_title}): Kurang {len(missing)} video!")
            for m in missing:
                print(f"   -> Hilang: {m}")
            total_missing += len(missing)

    print("\n=== RINGKASAN ===")
    print(f"Total Video Ditemukan : {total_found}")
    print(f"Total Video Hilang    : {total_missing}")


if __name__ == "__main__":
    main()