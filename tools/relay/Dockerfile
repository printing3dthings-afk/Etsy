FROM python:3.11-slim
WORKDIR /app
COPY tools/relay/requirements.txt tools/relay/requirements.txt
RUN pip install --no-cache-dir -r tools/relay/requirements.txt
COPY tools/relay/frank_relay.py tools/relay/frank_relay.py
# Run as a non-root user (2026-07-08 security review — no USER directive previously,
# ran as root by default). a+rwX keeps local-file-write tool calls working for a
# single-tenant private deployment regardless of exact uid.
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app \
    && chmod -R a+rwX /app
USER appuser
CMD ["python", "tools/relay/frank_relay.py"]
