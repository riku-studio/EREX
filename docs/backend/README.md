# 后端说明（FastAPI）

## 目录约定
- `app/main.py`：应用入口，注册路由与中间件。
- `app/routes/`：路由层（当前仅 `health`，后续按领域拆分）。
- `app/utils/`：配置与日志工具（`Config` 读取 `.env`，日志输出 stdout）。
- `app/core/`：预留公共依赖、异常处理、中间件。
- `app/models/` / `app/services/`：预留数据模型与业务服务实现。

## 运行方式
- 本地直接运行：`cd backend && uv run uvicorn app.main:app --reload --port 8000`（仅容器内暴露，dev 由前端/反代访问）。
- 容器化：`cd infra && docker compose up --build`，backend 以热重载方式运行，与 PostgreSQL 内网互通。

## 配置
- 读取根层 `.env`（模板 `.env.example`）；常用键：`APP_ENV`、`PORT`、`DB_HOST/PORT/USER/PASS/NAME`、日志开关。
- 数据库目前未在代码中使用，保留为后续持久化解析结果/模板的入口。

## 后续扩展建议
- 在 `app/routes/` 新增 API 时，同时在 `app/services/` 中实现业务逻辑，避免胖路由。
- Pipeline 模块可放置于 `app/services/pipeline/`（importer/cleaner/semantic/splitter/extractor/classifier/aggregator），按配置驱动启停。
- 定义 Pydantic 模型用于请求/响应校验，并在 `/docs` 自动生成 OpenAPI。
