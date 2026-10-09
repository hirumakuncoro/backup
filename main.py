import logging
import os
import subprocess
import sys
from pathlib import Path

import requests

# Konfigurasi Logging: tampil di console dan disimpan ke file download_errors.log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("download_errors.log")
    ]
)

# ============ CONFIG ============
START_INDEX = 1  # Ubah angka ini jika ingin melanjutkan nomor folder sebelumnya

COURSE_IDS = [
    10262,
    10349,
    10372,
    10385,
    10400,
    10411,
    10428,
    10437,
    10454,
    10467,
    10514,
    10955,
    11421,
    12702,
    12811,
    13657,
    15260,
    15514,
    16619,
    18722,
    19177,
    19581,
    20770,
    21419,
    25035,
    25128,
    25154,
    29926,
    29928,
    29944,
    30620,
    31021,
    31092,
    31106,
    31111,
    31113,
    31150,
    31153,
    31156,
    31158,
    31162,
    31164,
    31166,
    31184,
    31188,
    31192,
    33233,
    33421,
    34403,
    34830,
    35229,
    35247,
    35269,
    35284,
    35317,
    35319,
    35348,
    35419,
    35573,
    35584,
    35731,
    35736,
    35756,
    35765,
    35772,
    35778,
    35785,
    35796,
    35826,
    35851,
    35979,
    35987,
    35993,
    35999,
    36446,
    36449,
    36452,
    36856,
    37460,
    38605,
    41593,
    41597,
    42248,
    42902,
    43094,
    43867,
    43874,
    45125,
    45129,
    45959,
    46708,
    46869,
    47746,
    49092,
    49470,
    49472,
    49678,
    49781,
    50423,
    51241,
    52023,
    52564,
    53270,
    53531,
    54036,
    54738,
    55439,
    55977,
    57569,
    58945,
    60043,
    60567,
    60683,
    61390,
    61711,
    62426,
    66007,
    67525,
    69718,
    69761,
    70149,
    70332,
    70825,
    71239,
    71343,
    71955,
    72277,
    72724,
    73365,
    73829,
    73951,
    74856,
    75347,
    77898,
    79581,
    80043,
    80284,
    82051,
    82611,
    83122,
    83347,
    83751,
    84840,
    87202,
    88946,
    88951,
    88953,
    88956
]
PULL_ZONE = "vz-0e6889a5-f64"
QUALITY = "best[height<=1080]/best"  # Max 1080p, fallback to best available
API_TOKEN = os.environ.get("TOKEN", "")
TARGET_DOMAIN = os.environ.get("DOMAIN", "")
YTDLP_HEADERS = [
    "--referer", "https://iframe.mediadelivery.net/",
    "--add-header", "Origin: https://iframe.mediadelivery.net",
    "--add-header",
    "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
    "--downloader-args", "ffmpeg:-allowed_extensions ALL"
]
# ================================


def fetch_course(course_id: str) -> dict:
    url = f"https://{TARGET_DOMAIN}/api/v1/courses/{course_id}/modules"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "*/*",
        "Referer": f"https://{TARGET_DOMAIN}/academy/course/{course_id}",
        "x-client-type": "web",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/154.0.0.0 Safari/537.36",
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["data"]["course_modules"]


def extract_videos(course: dict) -> list[tuple[str, str, str]]:
    """Return list (section_title, lesson_title, video_id)."""
    videos = []
    for section in course.get("sections", []):
        section_title = section.get("section_title", section.get("title", "Unknown Section"))
        for lesson in section.get("lessons", []):
            url = lesson.get("video_url", "")
            if url and "mediadelivery.net/embed/" in url:
                video_id = url.rstrip("/").split("/")[-1]
                lesson_title = lesson.get("lesson_title", lesson.get("title", "Unknown Lesson"))
                videos.append((section_title, lesson_title, video_id))
    return videos


def sanitize(name: str) -> str:
    """Bersihkan nama file dari karakter ilegal."""
    for ch in r'/\:*?"<>|':
        name = name.replace(ch, "_")
    return name.strip()


def download(video_id: str, output_path: Path) -> bool:
    """Download 1080p ke output_path. Return True kalau sukses."""
    if output_path.exists():
        logging.info(f"File sudah ada: {output_path.name}, skip.")
        return True

    output_path.parent.mkdir(parents=True, exist_ok=True)

    hls = f"https://{PULL_ZONE}.b-cdn.net/{video_id}/playlist.m3u8"
    cmd = [
        "yt-dlp",
        *YTDLP_HEADERS,
        "-f", QUALITY,
        "--no-part",
        "-o", str(output_path),
        hls,
    ]
    logging.info(f"Mulai yt-dlp untuk {video_id}")

    # Capture output agar error bisa masuk ke log Python
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logging.error(f"yt-dlp gagal untuk {video_id}. Error:\n{result.stderr.strip()}")
        return False

    return True


def process_course(course_idx: int, course_id: str) -> None:
    logging.info(f"=== Course {course_id} ===")
    course = fetch_course(course_id)
    raw_title = sanitize(course.get("course_title", f"Course_{course_id}"))
    course_title = f"{course_idx:02d} - {raw_title}"
    videos = extract_videos(course)
    logging.info(f"{len(videos)} video ditemukan di '{course_title}'")

    base_dir = Path.cwd() / course_title

    for idx, (section_title, lesson_title, video_id) in enumerate(videos, 1):
        safe_section = sanitize(section_title)
        safe_lesson = sanitize(lesson_title)

        filename = f"{idx:02d} - {safe_lesson}.mp4"
        local_path = base_dir / safe_section / filename

        logging.info(f"[{idx}/{len(videos)}] {section_title} - {lesson_title}")
        if not download(video_id, local_path):
            logging.error(f"Download gagal: {local_path.name}")
        else:
            if local_path.exists():
                size_mb = local_path.stat().st_size / 1024 / 1024
                logging.info(f"Selesai ({size_mb:.1f} MB) → {local_path.relative_to(Path.cwd())}")


def main() -> None:
    if not API_TOKEN:
        logging.error("TOKEN tidak ditemukan di environment.")
        sys.exit(1)
    if not TARGET_DOMAIN:
        logging.error("DOMAIN tidak ditemukan di environment.")
        sys.exit(1)

    for idx, cid in enumerate(COURSE_IDS, START_INDEX):
        try:
            process_course(idx, str(cid))
        except Exception as e:
            logging.error(f"Course {cid} error: {e}")


if __name__ == "__main__":
    main()
