# API 说明

# API 说明

## 当前接口
- `GET /health`：健康检查。
- `GET /`：根路由示例。
- `GET /index-rules`：获取索引规则。
- `GET /pipeline/config`：查看当前 pipeline 配置与步骤。
- `POST /pipeline/upload`：上传 `pst/eml/msg` 到 `data/` 目录。
- `DELETE /pipeline/files`：删除 `data/` 中指定文件。
- `POST /pipeline/run`：执行 pipeline（cleaner → line_filter → semantic → splitter → extractor → classifier → aggregator），返回每封邮件聚合结果与总体摘要（邮件数、块数、关键字汇总、分类汇总）。

## 响应要点
- `/pipeline/run` 响应：
  - `results`: 每封邮件 `{source_path, subject, aggregation}`，aggregation 含 `block_count`、`keyword_summary`、`class_summary`（不返回块明细）。
  - `summary`: 总体统计（`message_count`、`block_count`、keyword/class 汇总）。
- 上传/删除：返回成功的文件列表或删除计数。

## 设计约定
- 统一使用 Pydantic 模型；OpenAPI 可通过 `/docs` / `/openapi.json` 查看。
- 配置与步骤由 `PIPELINE_STEPS` 驱动，可通过 `/pipeline/config` 确认。
