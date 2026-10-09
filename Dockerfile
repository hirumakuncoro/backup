FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
curl ca-certificates ffmpeg \
&& rm -rf /var/lib/apt/lists/*

# yt-dlp
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
-o /usr/local/bin/yt-dlp && chmod +x /usr/local/bin/yt-dlp

COPY --from=rclone/rclone:latest /usr/local/bin/rclone /usr/local/bin/rclone

RUN pip install --no-cache-dir requests pycryptodomex

WORKDIR /app
COPY main.py .

CMD ["python3", "main.py"]
