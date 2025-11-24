# syntax=docker/dockerfile:1
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装 uv
RUN pip install uv
# PST 支持：安装 readpst（libpst 提供）
RUN apt-get update \
    && apt-get install -y --no-install-recommends pst-utils \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY ./app ./app
COPY ./config ./config
COPY .env.example .env

# 启动命令
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
