FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Separate layer so pip stays cached when only grammar prefetch changes.
RUN python -c "from tree_sitter_language_pack import download; download(['python','javascript','typescript','tsx','java','go','rust','c','cpp'])"

COPY . .

RUN mkdir -p /app/workspaces /app/reports

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]



