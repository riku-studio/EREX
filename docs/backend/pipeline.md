# 后端邮件处理 Pipeline

## 流程概览
- 原始邮件 -> parser（`app/services/email_parser.py`） -> cleaner（`app/services/cleaner.py`） -> line_filter（`app/services/preprocess/line_filter.py`） -> semantic（`app/services/semantic.py`） -> 后续模块。
- cleaner 负责去除 HTML、压缩空白并保持换行。
- line_filter 对 cleaner 输出的行做轻量负向过滤，只删除明显无用的行。
- semantic 模块在过滤后的正文上做 sentence-transformer 相似度打分，接口保持 `extract(body: str)` 不变。

## 轻量行过滤的目的
- 在进入 embedding/语义阶段前先粗筛，减少需要编码的行数，降低 N100 负载。
- 只做「肯定是垃圾」的负向过滤；一旦行中包含招聘相关关键词（`Config.LINE_FILTER_JOB_KEYWORDS`），无条件保留，不删有效业务信息。
