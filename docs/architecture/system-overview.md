# 系统概述（System Overview）

EREX（Extensible Email Extraction System）是一套可配置、可扩展的邮件解析与语义提取平台，目标是通过配置文件驱动的 NLP 管道，从 EML/MSG/PST 等邮件中抽取结构化信息，并以前后端分离的方式呈现结果。

核心目标
- 模块化 Pipeline：各步骤可插拔、可配置，适配招聘、法务、投诉等多场景。
- 配置优先：正则、语义模板、关键词、分类规则均从版本化配置加载，不通过 Web 直接修改。
- 多容器一致性：React 前端 + FastAPI 后端 + PostgreSQL（预留），仅前端对宿主暴露端口，后端与数据库内部通信，便于将来接入反向代理或网关。
- 可渐进演进：数据库与高级模块可按阶段启用，不阻塞现阶段骨架开发。

主要组成
- Frontend（React，占位阶段由 Nginx 提供静态页，后续替换为构建产物）
- Backend（FastAPI，负责 API、Pipeline 编排、配置加载）
- Database（PostgreSQL，预留用于持久化原始邮件索引、解析结果、模板/统计数据）

配置与扩展入口（示例路径）
- 语义筛选模板：`config/templates/*.json`
- 分块规则：`config/patterns/*.json`
- 关键词字典：`config/keywords/*.json`
- 分类规则：`config/classifiers/*.json`

运行形态
- 本地/开发：通过 `infra/docker-compose.yml` 以多容器方式启动，frontend 暴露 `127.0.0.1:3000`，backend/db 仅内网可见。
- 生产：推荐由前端或网关反代后端 API，沿用相同 Dockerfile，按需启用数据库和日志采集。
