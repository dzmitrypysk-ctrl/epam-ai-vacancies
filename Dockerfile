FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service/ service/
COPY mcp_server/ mcp_server/
COPY data/jobs.json.gz data/jobs.json.gz
COPY data/indexnow.key data/indexnow.key
COPY data/removed_ids.json data/removed_ids.json
COPY data/google2016ac00a6475d2c.html data/google2016ac00a6475d2c.html

ENV HOST=0.0.0.0
ENV PORT=8977

EXPOSE 8977

CMD uvicorn service.app:app --host 0.0.0.0 --port ${PORT:-8977}
