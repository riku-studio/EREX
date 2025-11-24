# 后端说明（FastAPI）

## 目录约定
- `app/main.py`：应用入口，注册路由与中间件。
- `app/routes/`：路由层（当前包含 `health`、`index_rules`）。
- `app/utils/`：配置与日志工具（`Config` 读取 `.env`，日志输出 stdout）。
- `app/core/`：预留公共依赖、异常处理、中间件。
- `app/models/` / `app/services/`：预留数据模型与业务服务实现；`services/index_rules.py` 支持文件/数据库双源读取索引规则并向 Pipeline 提供统一接口（Pipeline 不感知来源）。

## 运行方式
- 本地直接运行：`cd backend && uv run uvicorn app.main:app --reload --port 8000`（仅容器内暴露，dev 由前端/反代访问）。
- 容器化：默认文件模式 `cd infra && docker compose up --build`；若启用数据库索引规则，执行 `docker compose --profile db up --build` 以启动 PostgreSQL。

## 配置
- 读取根层 `.env`（模板 `.env.example`）；常用键：`APP_ENV`、`PORT`、`DB_HOST/PORT/USER/PASS/NAME`、日志开关。
- 索引规则来源：`INDEX_RULE_SOURCE=file|db`（默认 file），`INDEX_RULES_PATH`（文件路径，默认 `backend/config/index_rules.json`），`INDEX_RULE_TABLE`（数据库模式下的表名）。
- 数据库仅在 `INDEX_RULE_SOURCE=db` 时需要；镜像内已包含 `asyncpg` 以便直接连接，启用数据库时配合 compose `db` profile。

## 后续扩展建议
- 在 `app/routes/` 新增 API 时，同时在 `app/services/` 中实现业务逻辑，避免胖路由。
- Pipeline 模块可放置于 `app/services/pipeline/`（importer/cleaner/semantic/splitter/extractor/classifier/aggregator），按配置驱动启停。
- 定义 Pydantic 模型用于请求/响应校验，并在 `/docs` 自动生成 OpenAPI。
