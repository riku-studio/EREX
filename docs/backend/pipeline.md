# 后端邮件处理 Pipeline（配置化）

## 流程概览
- 原始邮件 -> parser（`app/services/email_parser.py`） -> cleaner（`app/services/cleaner.py`） -> line_filter（`app/services/preprocess/line_filter.py`） -> semantic（`app/services/semantic.py`） -> splitter（`app/services/splitter.py`） -> extractor（`app/services/extractor.py`） -> classifier（`app/services/classifier.py`） -> aggregator（`app/services/aggregator.py`）。
- cleaner：去除 HTML、压缩空白并保持换行。
- line_filter：轻量负向过滤，只删除明确垃圾行；命中招聘关键词（配置 `LINE_FILTER_JOB_KEYWORDS`）则保留。
- semantic：按行构造上下文 segment（行 ± `context_radius`），基于多模板（global + fields）一次性 embedding 做相似度筛选，模板与阈值来自 `backend/config/semantic_job_templates.json`。
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
