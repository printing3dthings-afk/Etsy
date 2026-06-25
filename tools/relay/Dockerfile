FROM python:3.11-slim
WORKDIR /app
COPY tools/relay/requirements.txt tools/relay/requirements.txt
RUN pip install --no-cache-dir -r tools/relay/requirements.txt
COPY tools/relay/frank_relay.py tools/relay/frank_relay.py
CMD ["python", "tools/relay/frank_relay.py"]
