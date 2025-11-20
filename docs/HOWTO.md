# 快速启动指南（设计阶段骨架）

1. 复制环境变量模板：`cp .env.example .env`，按需修改端口或数据库口令。
2. 启动多容器开发环境：
   ```bash
   cd infra
   docker compose up --build
   ```
3. 验证：
   - 后端健康检查：`curl http://localhost:8000/health`
   - 前端占位页：浏览器打开 `http://localhost:3000`

提示：当前前端为 Nginx 占位，后端 FastAPI 仅包含基础路由。后续替换前端为 React 构建产物、按需求扩展后端路由与服务层。
