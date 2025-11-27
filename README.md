# EREX

## About
EREX 是一套以语义理解（Semantic Understanding）为核心的邮件数据抽取平台，利用 Transformer Embedding 技术实现对邮件内容的深度语义匹配、块级智能分割与意图识别。通过配置驱动的 NLP 管道，EREX 能够从 PST/MSG/EML 等海量邮件中自动识别领域语义、抽取关键要素，并转换为结构化数据，为企业信息处理提供智能化、自动化支撑。

### 核心能力
- **语义筛选**：Sentence-Transformers 向量相似度 + 模板匹配，自动捕捉与招聘/业务相关的语义片段。
- **轻量行过滤**：规则化去噪（签名、免责声明、装饰行等），降低 embedding 开销。
- **块级分割**：按“案件/案件名”等标记拆分多块内容，支持多职位/多段识别。
- **关键字抽取 & 分类**：配置化技术词典、正则分类器，生成统计与标签。
- **聚合与洞察**：按邮件/全局汇总块数、关键字、分类分布；可调用 OpenAI 获取技术说明（tech insight）。
- **前后端分离**：FastAPI 后端 + Vite/React 前端，提供上传、运行、可视化、关键词点击洞察等界面。

## 快速开始（Docker）
### 1. 环境准备
- 安装 Docker / Docker Compose
- 在仓库根目录创建 `.env`（参考 `.env.example`），填写必要配置：
  - `OPENAI_API_KEY`（可选，用于 tech-insight）
  - 其他服务参数（端口、日志、数据库等）

### 2. 构建并启动
```bash
cd infra
# 前后端一并启动（前端 3000/8002，后端 8000 映射到本机）
docker compose up --build
```
> 若需要重新构建：`docker compose build`。

### 3. 访问
- 前端：`http://localhost:8002`（或配置的域名/端口），提供上传、运行、配置查看、可视化等功能。
- 后端 API：`http://localhost:8000`，可通过 `/docs` 查看 OpenAPI。

## 主要接口
- `GET /pipeline/config`：查看当前 pipeline 配置与步骤。
- `POST /pipeline/upload` / `DELETE /pipeline/files` / `GET /pipeline/files`：文件管理（pst/eml/msg）。
- `POST /pipeline/run`：运行完整 pipeline（cleaner → line_filter → semantic → splitter → extractor → classifier → aggregator）。
- `POST /pipeline/tech-insight`：基于关键字统计调用 OpenAI（如未配置 key 则返回占位说明）。

## 开发说明
- 后端：`backend`，FastAPI + uv；`uv run uvicorn app.main:app --reload` 本地开发。
- 前端：`frontend`，Vite + React；`npm install && npm run dev` 本地开发。Docker 镜像内 Nginx 反代 `/pipeline/*` 到后端。

## 目录结构（关键部分）
- `backend/app/services/`：cleaner、line_filter、semantic、splitter、extractor、classifier、aggregator、pipeline 等核心模块。
- `backend/config/`：语义模板、行过滤规则、关键字词典、分类器规则。
- `frontend/`：Vite/React 前端代码与 Nginx 配置。
- `infra/`：Docker Compose 配置。

## 提示
- 默认 pipeline 步骤可通过 `PIPELINE_STEPS` 控制。
- 大文件上传已在前端 Nginx 放宽 `client_max_body_size`，长任务超时（反代）默认 30 分钟，可按需调整。
