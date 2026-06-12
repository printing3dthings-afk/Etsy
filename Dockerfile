FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir \
    fastapi==0.111.0 \
    "uvicorn[standard]==0.29.0" \
    "anthropic>=0.28.0" \
    python-dotenv==1.0.1
EXPOSE 8000
CMD ["/bin/sh", "-c", "uvicorn tools.api_server.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
