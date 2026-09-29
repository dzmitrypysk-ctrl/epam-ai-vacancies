FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service/ service/
COPY mcp_server/ mcp_server/
COPY data/jobs.json.gz data/jobs.json.gz

ENV HOST=0.0.0.0
ENV PORT=8977

EXPOSE 8977

CMD uvicorn service.app:app --host 0.0.0.0 --port ${PORT:-8977}
