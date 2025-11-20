# 前端说明（React）

## 现状
- `frontend/Dockerfile` 使用 Nginx 提供静态内容，目前放置占位页 `frontend/public/index.html`。
- 前端端口在 dev 模式下绑定 `127.0.0.1:3000`，通过反代访问 backend。

## 建议落地路径
1. 使用 Vite 初始化 React 工程（`frontend/src`、`public`），保留 `Dockerfile` 作为生产静态发布镜像。
2. 构建产物输出到 `dist/`，Dockerfile 中以多阶段方式复制至 `/usr/share/nginx/html`。
3. 在 `.env` 或构建命令中注入 `API_BASE_URL`，与反向代理配置保持一致。
4. 如需本地开发热更新，可在 Compose 增加 dev server 命令（`npm run dev -- --host --port 3000`）并挂载源代码。

## 路由与页面（规划）
- Dashboard：展示解析统计与最近任务。
- Templates：配置预览与说明（只读，源自版本库的配置文件）。
- Tasks/Results：展示单次解析结果与详情。
- Health：前端健康页，可嵌入 backend `/health` 检查。
