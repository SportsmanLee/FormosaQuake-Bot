# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# copy lock + manifest
COPY pyproject.toml uv.lock ./

# Install uv
RUN pip install --no-cache-dir uv==0.9.18

# Sync dependencies (no dev; frozen lock)
RUN uv sync --frozen

COPY src ./src

# Data dir for sqlite
RUN mkdir -p /data

# Default envs (override in runtime)
ENV SQLITE_PATH=/data/bot.db \
    TZ=Asia/Taipei

CMD ["uv", "run", "python", "-m", "src.app"]