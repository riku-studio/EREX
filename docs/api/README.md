# API 说明（Backend）

## 基础
- `GET /health`：健康检查，`200 {"status": "ok"}`。
- `GET /`：根路由示例。
- `GET /index-rules`：返回索引规则列表。
- `POST /pipeline/tech-insight`：基于关键字统计（`keyword/count/ratio`）调用 OpenAI 生成简短技术介绍。

## Pipeline 配置
### `GET /pipeline/config`
- 响应 `200`：
  ```json
  {
    "summary": { ...Config.summary()... },
    "steps": ["cleaner", "line_filter", "semantic", "splitter", "extractor", "classifier", "aggregator"]
  }
  ```

## 文件上传/删除
### `POST /pipeline/upload`
- Content-Type: `multipart/form-data`
- 字段：`files[]`（支持多个 pst/eml/msg）
- 响应 `200`：
  ```json
  [
    {"filename": "sample.eml", "size": 12345},
    {"filename": "sample.msg", "size": 6789}
  ]
  ```

### `DELETE /pipeline/files`
- Body（JSON 数组）：`["sample.eml", "sample.msg"]`
- 响应 `200`：
  ```json
  {"deleted": 2, "skipped": 0}
  ```

## 运行 Pipeline
### `POST /pipeline/run`
- 无请求体；读取 `data/` 下全部 pst/eml/msg 并运行步骤：
  cleaner → line_filter → semantic → splitter → extractor → classifier → aggregator
- 响应 `200`：
  ```json
  {
    "results": [
      {
        "source_path": "...",
        "subject": "...",
        "semantic": {
          "text": "...", "score": 0.72,
          "start_line": 3, "end_line": 8,
          "matched": true,
          "line_scores": [0.1, 0.2, ...]
        },
        "aggregation": {
          "block_count": 2,
          "keyword_summary": {
            "programming_languages": [
              {"keyword": "Python", "count": 1, "ratio": 0.5},
              {"keyword": "Go", "count": 1, "ratio": 0.5}
            ]
          },
          "class_summary": {
            "ok": {"count": 1, "ratio": 0.5},
            "ng": {"count": 1, "ratio": 0.5}
          }
        }
      }
    ],
    "summary": {
      "message_count": 10,
      "block_count": 15,
      "keyword_summary": { ... 全部块汇总，同上结构 ... },
      "class_summary": { ... 全部块汇总，同上结构 ... }
    }
  }
  ```
- 说明：
  - `semantic`：语义匹配结果；若未命中或语义步骤关闭则为 `null`。
  - `aggregation.block_count`：该邮件分出的块数（不返回块明细）。
  - `keyword_summary` / `class_summary`：按类别汇总的计数与比例（比例 = count / 块总数）。
- `summary`：所有邮件整体汇总。

### `POST /pipeline/tech-insight`
- 请求体：
  ```json
  {
    "keyword": "Python",
    "count": 10,
    "ratio": 0.25,
    "category": "programming_languages"
  }
  ```
- 响应 `200`：
  ```json
  {"keyword": "Python", "insight": "…简短介绍，包含出现比例含义…"}
  ```
- 说明：需配置 `OPENAI_API_KEY`（可选 `OPENAI_MODEL`），依赖 openai 包；未配置时返回 503。

## 设计约定
- OpenAPI：访问 `/docs` 或 `/openapi.json`。
- 配置驱动：`PIPELINE_STEPS` 控制启用的模块；可通过 `/pipeline/config` 查询当前生效步骤。***
