# 部署与运行指南

## 开发环境（docker-compose）
1. 复制环境变量模板：`cp .env.example .env`，按需修改端口/数据库口令。
2. 启动：`cd infra && docker compose up --build`
   - frontend：127.0.0.1:3000 对宿主开放（Nginx 占位）。
   - backend：容器内 8000，仅供内部网络；前端/反代访问。
   - db：PostgreSQL 16，仅容器网络。
3. 验证：
   - `curl http://127.0.0.1:3000` 查看占位页。
   - `docker compose exec backend curl http://backend:8000/health`

## 生产/准生产（示例流程）
- 构建并推送镜像：`docker build -t <registry>/erex-backend:<tag> backend/`，`docker build -t <registry>/erex-frontend:<tag> frontend/`。
- 部署：在服务器上准备 `.env`，执行 `docker compose -f infra/docker-compose.yml up -d` 或专用 prod compose；仅暴露前端端口，由前端或独立网关反向代理 backend。
- 日志：全部输出 stdout/stderr，可接入 Loki/ELK；无本地日志文件。

## 配置约定
- 所有服务依赖根层 `.env`；敏感值不提交版本库。
- 端口策略：对外只开放前端；backend/db 通过容器网络访问。
- 可选组件：若暂不需要数据库，可在 compose 中注释 db 服务。
