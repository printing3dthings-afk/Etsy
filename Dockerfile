FROM python:3.11-slim
# build-4
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir \
    fastapi==0.111.0 \
    "uvicorn[standard]==0.29.0" \
    "anthropic>=0.28.0" \
    "openai>=1.0.0" \
    "PyPDF2>=3.0.0" \
    python-dotenv==1.0.1 \
    "moviepy>=2.0" \
    numpy \
    "Pillow>=10.0" \
    imageio-ffmpeg
EXPOSE 8000
CMD ["python", "tools/api_server/main.py"]
