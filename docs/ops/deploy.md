# 部署与运行指南

## 开发环境（docker-compose）
1. 复制环境变量模板：`cp .env.example .env`，按需修改端口/数据库口令。
2. 选择索引规则存储方式：
   - 配置文件（默认）：保持 `INDEX_RULE_SOURCE=file`，规则从 `backend/config/index_rules.json` 读取；无需启动数据库。
   - 数据库：设置 `INDEX_RULE_SOURCE=db`，可选指定 `INDEX_RULE_TABLE`；需要安装数据库驱动（如 asyncpg）并启动 `db` 服务。
3. 启动：
   - 文件模式：`cd infra && docker compose up --build`
   - 数据库模式：`cd infra && docker compose --profile db up --build`
     - frontend：127.0.0.1:3000 对宿主开放（Nginx 占位）。
     - backend：容器内 8000，仅供内部网络；前端/反代访问。
     - db（仅 database profile）：PostgreSQL 16，仅容器网络。
4. 验证：
   - `curl http://127.0.0.1:3000` 查看占位页。
   - `docker compose exec backend curl http://backend:8000/health`
   - `docker compose exec backend curl http://backend:8000/index-rules` 查看当前索引规则来源。

## 生产/准生产（示例流程）
- 构建并推送镜像：`docker build -t <registry>/erex-backend:<tag> backend/`，`docker build -t <registry>/erex-frontend:<tag> frontend/`。
- 部署：在服务器上准备 `.env`，执行 `docker compose -f infra/docker-compose.yml up -d` 或专用 prod compose；仅暴露前端端口，由前端或独立网关反向代理 backend。
- 日志：全部输出 stdout/stderr，可接入 Loki/ELK；无本地日志文件。

## 配置约定
- 所有服务依赖根层 `.env`；敏感值不提交版本库。
- 端口策略：对外只开放前端；backend/db 通过容器网络访问。
- 可选组件：默认不启动数据库；当 `INDEX_RULE_SOURCE=db` 时使用 `--profile db` 追加数据库服务，并确保容器包含数据库驱动。
