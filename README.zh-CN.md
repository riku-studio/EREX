# EREX

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

EREX 是一个基于语义理解的邮件数据抽取平台，通过可配置的 NLP 流水线与向量语义匹配，实现从 PST/MSG/EML 等邮件中抽取结构化信息。

## 功能特性

- 基于 Sentence-Transformers 的语义筛选。
- 轻量行过滤（签名、免责声明、装饰行等去噪）。
- 多块内容分割（支持多职位邮件拆分）。
- 配置化关键词抽取与规则分类。
- 汇总统计与可选 LLM 技术说明（tech insight）。
- 前后端分离架构（FastAPI + React/Vite）。

## 快速开始

### 环境准备

- 安装 Docker / Docker Compose
- 在仓库根目录创建 `.env`（参考 `.env.example`）

### Docker 启动

```bash
cd infra
docker compose up --build
```

### 访问地址

- 前端：`http://localhost:8002`
- 后端：`http://localhost:8000`
- OpenAPI：`http://localhost:8000/docs`

## 语义计算 CPU/GPU 切换

在 `.env` 中配置：

- `SEMANTIC_ACCELERATOR=cpu|gpu|auto`
- `SEMANTIC_DEVICE=`（可选，如 `cuda:0`）

容器内检查 GPU：

```bash
cd infra
docker compose exec backend nvidia-smi
```

## 主要接口

- `GET /pipeline/config`
- `POST /pipeline/upload`
- `GET /pipeline/files`
- `DELETE /pipeline/files`
- `POST /pipeline/run`
- `POST /pipeline/run/start`
- `GET /pipeline/run/{job_id}/progress`
- `GET /pipeline/run/{job_id}/result`
- `POST /pipeline/history`
- `GET /pipeline/history`
- `GET /pipeline/history/{id}`
- `DELETE /pipeline/history/{id}`
- `POST /pipeline/tech-insight`

## 本地开发

### 后端

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 配置来源

Pipeline 配置默认从文件加载。数据库可用时会切换为 `db` 来源；不可用则回退为 `file`。

## 目录结构

- `backend/app/services/` 核心流水线模块
- `backend/config/` 语义模板、关键词词典、规则配置
- `frontend/` Web 前端
- `infra/` Docker 相关配置
- `docs/` 架构与模块文档

## 许可证

见 `LICENSE.md`。
