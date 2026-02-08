# 后端邮件处理 Pipeline（配置化）

## 流程概览
- 原始邮件 -> parser（`app/services/email_parser.py`） -> cleaner（`app/services/cleaner.py`） -> line_filter（`app/services/preprocess/line_filter.py`） -> semantic（`app/services/semantic.py`） -> splitter（`app/services/splitter.py`） -> extractor（`app/services/extractor.py`） -> classifier（`app/services/classifier.py`） -> aggregator（`app/services/aggregator.py`）。
- cleaner：去除 HTML、压缩空白并保持换行。
- line_filter：轻量负向过滤，只删除明确垃圾行；命中招聘关键词（配置 `LINE_FILTER_JOB_KEYWORDS`）则保留。
- semantic：对过滤后的正文执行连续窗口搜索（`min_lines..window_max_lines`），按正向模板匹配、负向模板抑制、长度项与中心位置加权综合打分；随后做高分窗口簇合并与头尾负向裁剪（签名/公司信息/免责声明等），模板与阈值来自 `backend/config/semantic_job_templates.json`，结果返回在 `/pipeline/run` 的 `semantic` 字段。
- splitter：按“案件/案件名”独立行切分，一封邮件内可拆出多个招聘块（默认跳过首尾 5 行的标记）。
- extractor：从配置化技术关键字（`backend/config/keywords_tech.json`）提取并汇总出现次数/比例（块内去重）。
- classifier：示例 `foreigner` 分类器（`backend/config/classifiers/foreigner.json`）基于正则判断可/不可；可扩展其他分类。
- aggregator：汇总块数量、关键字统计、分类统计；不返回块明细。

## 轻量行过滤的目的
- 在进入 embedding/语义阶段前先粗筛，减少需要编码的行数，降低模型负载。
- 只做「肯定是垃圾」的负向过滤；命中招聘关键词时无条件保留，避免误删有效信息。

## Pipeline 配置
- `Config.PIPELINE_STEPS` 控制启用步骤（默认：`cleaner,line_filter,semantic,splitter,extractor,classifier,aggregator`）。
- 上传/删除/运行接口：`/pipeline/upload`、`/pipeline/files`、`/pipeline/run`，配置查看：`/pipeline/config`。
- 异步运行接口：`POST /pipeline/run/start`、`GET /pipeline/run/{job_id}/progress`、`GET /pipeline/run/{job_id}/result`。
- 历史记录接口（手动保存）：`POST /pipeline/history`、`GET /pipeline/history`、`GET /pipeline/history/{id}`、`DELETE /pipeline/history/{id}`。

## 历史记录行为
- 默认不自动保存运行结果。
- 前端用户点击保存后，后端将本次 `PipelineRunResponse` 落盘到 `data/history/*.json`。
- 历史列表按保存时间倒序展示，可查看详情并删除指定记录。
