FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Create run.sh in-container to avoid CRLF / copy issues
RUN printf '%s\n' \
  '#!/bin/sh' \
  'set -e' \
  'PORT="${PORT:-8080}"' \
  'exec streamlit run app.py --server.port "$PORT" --server.address 0.0.0.0 --server.headless true' \
  > /app/run.sh && chmod +x /app/run.sh

EXPOSE 8080
ENV PORT=8080
CMD ["./run.sh"]
