# 数据库设计（预留）

## 现状
- docker-compose 通过 `--profile db` 提供 PostgreSQL 16 服务，默认不启动。
- 索引规则可读取数据库表（`INDEX_RULE_TABLE`），无需强制启用数据库：默认从配置文件读取，切换到 `INDEX_RULE_SOURCE=db` 才会访问此表。
- 主要用途：索引/分块/分类规则、原始邮件索引、解析结果、模板/规则版本、统计汇总。

## 规划要点
- 模式建议：`core`（系统表、任务、模板）、`analysis`（解析结果、分块、关键词命中）、`audit`（操作日志）。
- 连接方式：环境变量 `DB_HOST/DB_PORT/DB_USER/DB_PASS/DB_NAME`，在 `Config` 中读取；索引表名由 `INDEX_RULE_TABLE` 控制。
- 迁移工具：待功能落地后再确定（如 Alembic），当前无迁移脚本。

## 何时可以关闭数据库
- 若短期仅需演示 API 与前端占位，可保持文件模式并不启用 `db` profile；切换到数据库模式时再开启服务并补充迁移。 
