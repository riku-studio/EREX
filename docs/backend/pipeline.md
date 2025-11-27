# 后端邮件处理 Pipeline

## 流程概览
- 原始邮件 -> parser（`app/services/email_parser.py`） -> cleaner（`app/services/cleaner.py`） -> line_filter（`app/services/preprocess/line_filter.py`） -> semantic（`app/services/semantic.py`） -> 后续模块。
- cleaner 负责去除 HTML、压缩空白并保持换行。
- line_filter 对 cleaner 输出的行做轻量负向过滤，只删除明显无用的行。
- semantic 模块使用过滤后的正文，按行构造上下文 segment（行 ± `context_radius`），基于多模板（global + fields）一次性 embedding 做相似度筛选，接口保持 `extract(body: str)` 不变，模板与阈值来自 `backend/config/semantic_job_templates.json`。
- splitter（`app/services/splitter.py`）可按“案件/案件名”独立行切分，一封邮件内的多个招聘块将拆分成独立段落（默认跳过首尾 5 行的标记）。

## 轻量行过滤的目的
- 在进入 embedding/语义阶段前先粗筛，减少需要编码的行数，降低 N100 负载。
- 只做「肯定是垃圾」的负向过滤；一旦行中包含招聘相关关键词（`Config.LINE_FILTER_JOB_KEYWORDS`），无条件保留，不删有效业务信息。
