# 技术栈（Tech Stack）

| 层级         | 技术与工具                                     | 说明                          |
| ------------ | ---------------------------------------------- | ----------------------------- |
| 后端         | FastAPI + Uvicorn（uv 运行）                   | REST API、Pipeline 编排       |
| 前端         | React（Vite 推荐）+ Nginx 静态发布             | SPA，当前为占位静态页         |
| 数据库（预留）| PostgreSQL 16                                  | 持久化解析结果/模板/统计      |
| NLP/解析     | email/pypff/extract_msg + sentence-transformers | 邮件解析、语义匹配（按需启用）|
| 分块/抽取    | 正则 + 配置驱动（patterns/keywords/classifiers）| 规则从配置文件加载            |
| 配置管理     | dotenv + JSON/YAML 配置文件                    | 不在 Web 端直接修改           |
| 部署与本地   | Dockerfile + docker-compose                    | 多容器前后端分离              |
| 日志         | Python logging → stdout                        | 便于容器化收集                |
