# EREX Frontend

当前仅提供占位的静态页面，便于多容器编排与 Nginx 验证。后续请按 React 技术栈替换：

1. 使用 Vite/CRA 初始化 React 工程，保留 `frontend/Dockerfile` 作为生产静态服务镜像入口。
2. 将构建产物输出到 `dist/` 或 `build/`，在 Dockerfile 中 `COPY --from=build` 或直接复制到 `/usr/share/nginx/html`。
3. 更新 `infra/docker-compose.yml` 中前端服务的构建命令（如需 dev server 则改用 `npm run dev -- --host`）。

占位页面路径：`frontend/public/index.html`。
