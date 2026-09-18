FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY shared/python /tmp/bhoomi_common_src
RUN pip install --no-cache-dir /tmp/bhoomi_common_src && rm -rf /tmp/bhoomi_common_src

COPY services/search/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/search/app/ app/
RUN mkdir -p /app/logs

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
