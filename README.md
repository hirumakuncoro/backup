# Downloader

## Persiapan dengan Docker
Gunakan Docker agar tidak perlu install dependensi & `yt-dlp` manual di laptop.

1. Sesuaikan env variable (buat file `.env` jika belum ada):
   ```ini
   TOKEN=token-api-kamu
   DOMAIN=domain-target-kamu
   ```
2. Build image docker:
   ```bash
   docker compose build
   ```

## Cara Jalankan (Pake Docker)

### 1. Download Semua Course (`main.py`)
Download berdasarkan list ID course di script.
```bash
docker compose run --rm backup python3 main.py
```
*(Atau cukup `docker compose up` karena `main.py` adalah command default)*

### 2. Verifikasi File (`verify.py`)
Cek video yang kurang, ukurannya mencurigakan, atau error.
```bash
docker compose run --rm backup python3 verify.py
```

### 3. Download Video Spesifik (`download_single.py`)
Download video tertentu yang ID-nya sudah dimasukkan di dalam code.
1. Buka `download_single.py` di text editor.
2. Edit list `VIDEOS_TO_DOWNLOAD` dengan format `("video_id", "Nama Video")`. Bisa lebih dari satu.
3. Jalankan script pakai docker:
```bash
docker compose run --rm backup python3 download_single.py
```