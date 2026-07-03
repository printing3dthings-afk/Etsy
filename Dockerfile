FROM python:3.11-slim
# build-7
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
# Install from the canonical manifest (single source of truth) so the image can't
# drift out of sync with the app's real dependencies — the old hand-picked list had
# silently dropped requests/bs4/lxml (browse_web/search_etsy), google-genai (Veo /
# Nano Banana / video understanding), python-multipart (login form), and more.
# numpy comes in transitively via moviepy/Pillow.
RUN pip install --no-cache-dir -r requirements.txt
# Install Chromium + its system libraries for Frank's browser tools
# (tools/browser_automation.py). --with-deps pulls the required apt packages.
# playwright itself is installed via requirements.txt above.
RUN playwright install --with-deps chromium
ENV IMAGEIO_FFMPEG_EXE=/usr/bin/ffmpeg
EXPOSE 8000
CMD ["python", "tools/api_server/main.py"]
