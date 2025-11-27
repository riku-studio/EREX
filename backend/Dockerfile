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

# 复制依赖并安装
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 复制源码与配置
COPY ./app ./app
COPY ./config ./config

# 启动命令（生产模式）
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
