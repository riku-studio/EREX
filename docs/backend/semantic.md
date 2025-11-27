# Semantic 抽取说明

## 配置来源
- 路径：`backend/config/semantic_job_templates.json`
- 结构：
  - `context_radius`：构造上下文 segment 时包含的前后行数。
  - `global_threshold`：判断 segment 是否为求人块的全局阈值。
  - `field_threshold`：字段级标签（skill/contract 等）判定的参考阈值。
  - `global`: `string[]`，求人数检测的模板集合。
  - `fields`: `{ [field: string]: string[] }`，字段级模板列表（如 overview / work_content / skill / working_conditions / contract / restriction）。

## 处理流程
1. cleaner 后的正文通过 `LineFilter` 做轻量负向过滤（去问候、签名、免责声明等）。
2. 将过滤结果按行切分，移除空行。
3. 以 `context_radius` 为窗口，为每一行构造一个 segment（当前行 ± N 行，换行拼接）。
4. 对全部 segment 一次性 embedding，并与 `global` 模板向量求最大相似度，超过 `global_threshold` 的 segment 视为求人相关。
5. 将命中 segment 的起止行合并，输出 `SemanticResult`：
   - `text`: 覆盖行拼接后的正文
   - `score`: 命中 segment 的平均相似度
   - `start_line` / `end_line`: 覆盖行区间（基于过滤后的行索引）
   - `matched`: 是否存在命中 segment
   - `line_scores`: 每行的得分（覆盖该行的 segment 最大值）
6. 字段级模板会在内部计算各字段的最大相似度，作为调试/扩展用，不影响当前返回结构。

## 日志
- info 级：segment 总数、`global_threshold`、top segment 分数示例。
- debug 级：各字段模板的最高相似度，便于阈值调试。

## 对外接口
- `SemanticExtractor.extract(body: str) -> SemanticResult`，对调用方保持兼容。
- `Config.semantic_global_templates()` / `Config.semantic_field_templates()`：访问模板；`Config.SEMANTIC_CONTEXT_RADIUS`、`Config.SEMANTIC_JOB_GLOBAL_THRESHOLD`、`Config.SEMANTIC_JOB_FIELD_THRESHOLD` 提供相关阈值。
