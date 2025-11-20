# 架构设计（Architecture Design）

## 高层架构
```
Browser
   |
   | HTTP
   v
+----------+      +-----------------+      +----------------------+
| Frontend | ---> |  Reverse Proxy  | ---> |   Backend (FastAPI)  |
| React    |      |  (未来可接入)   |      |  Pipeline + Config   |
+----------+      +-----------------+      +----------+-----------+
                                                     |
                                                     v
                                           PostgreSQL (预留)
```
- 开发态：`infra/docker-compose.yml` 启动 frontend、backend、PostgreSQL，只有 frontend 绑定 `127.0.0.1:3000`；backend/db 仅容器网络可见。
- 生产态：沿用相同镜像，由前端或独立网关反向代理 backend，不直接暴露 backend/db。

## 服务职责
- Frontend（React + Nginx 静态发布）：呈现解析结果、配置预览与操作入口（当前为占位页，后续替换为构建产物）。
- Backend（FastAPI）：提供 REST API、调用管线 orchestrator、加载配置模板、记录审计日志（stdout）。
- Database（PostgreSQL，可按阶段启用）：存储原始邮件索引、解析后的结构化结果、模板与统计数据；若短期无需持久化，可停用服务。

## 目录与边界
- `backend/app`: 路由层（`routes/`）、配置与核心工具（`utils/`、`core/`）、未来的模型与服务层（`models/`、`services/`）。
- `frontend/`: React 工程目录，当前放置占位静态页面，Dockerfile 负责生产静态发布。
- `infra/`: Compose 定义与后续部署脚本；dev/prod 均以该目录为入口。
- `docs/`: 架构、前后端说明、ops、安全、测试等文档。

## 配置与运行
- 环境变量：使用根层 `.env`（模板见 `.env.example`），后端通过 `Config` 读取；前端可在构建时注入 `API_BASE_URL` 等变量。
- 端口策略：frontend 暴露 3000（本地绑定 127.0.0.1），backend 在容器内监听 8000，由前端/反代转发；数据库仅容器内访问。
- 日志：统一 stdout/stderr 输出，方便 Docker/集中日志采集。

## 可扩展性
- Pipeline 以模块目录划分（importer/cleaner/semantic/splitter/extractor/classifier/aggregator），可通过配置开启/关闭或替换实现。
- 新服务（如 Worker）可在 `infra/docker-compose.yml` 中追加独立容器，保持与 backend 的接口清晰分离。
