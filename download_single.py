import logging
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

PULL_ZONE = "vz-0e6889a5-f64"
QUALITY = "best[height<=1080]/best"
YTDLP_HEADERS = [
    "--referer", "https://iframe.mediadelivery.net/",
    "--add-header", "Origin: https://iframe.mediadelivery.net",
    "--add-header",
    "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
    "--downloader-args", "ffmpeg:-allowed_extensions ALL"
]

# DAFTAR VIDEO YANG INGIN DIDOWNLOAD
# Format: ("video_id", "Nama File Video")
VIDEOS_TO_DOWNLOAD = [
    ("19b8fad6-777d-46fa-a895-5d65e0286b9d", "Contoh Video 1"),
    # Tambahkan video lain di sini:
    # ("id_lain", "Nama Video Lain"),
]

def sanitize(name: str) -> str:
    for ch in r'/\:*?"<>|':
        name = name.replace(ch, "_")
    return name.strip()

def download(video_id: str, video_name: str) -> None:
    safe_name = sanitize(video_name)
    if not safe_name.endswith(".mp4"):
        safe_name += ".mp4"

    output_path = Path.cwd() / safe_name

    if output_path.exists():
        logging.info(f"File sudah ada: {output_path.name}")
        return

    hls = f"https://{PULL_ZONE}.b-cdn.net/{video_id}/playlist.m3u8"
    cmd = [
        "yt-dlp",
        *YTDLP_HEADERS,
        "-f", QUALITY,
        "--no-part",
        "-o", str(output_path),
        hls,
    ]

    logging.info(f"Mulai download: {video_id} -> {output_path.name}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        logging.error(f"Download gagal untuk: {video_name}")
    else:
        logging.info(f"Download selesai: {video_name}")

if __name__ == "__main__":
    if not VIDEOS_TO_DOWNLOAD:
        logging.warning("Daftar video kosong. Isi list VIDEOS_TO_DOWNLOAD di dalam script.")

    for vid, vname in VIDEOS_TO_DOWNLOAD:
        download(vid, vname)
