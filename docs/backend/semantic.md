# Semantic 抽取说明

## 配置来源
- 参数路径：`backend/config/semantic_job_templates.json`
- 正向模板路径：`backend/config/semantic_pos_templates.json`
- 负向模板路径：`backend/config/semantic_neg_templates.json`
- 测试模板（可用于迭代调参）：`backend/config/semantic_job_templates_test.json`
- 运行设备（`.env`）：
  - `SEMANTIC_ACCELERATOR=cpu|gpu|auto`：语义计算模式开关。
  - `SEMANTIC_DEVICE=`：可选设备覆盖（如 `cpu` / `cuda` / `cuda:0` / `mps`），优先级高于 `SEMANTIC_ACCELERATOR`。
  - 当 `SEMANTIC_ACCELERATOR=gpu|auto` 且 CUDA 可用时，运行设备自动选择 `cuda`，否则回退 `cpu`。
- 结构：
  - `context_radius`：构造上下文 segment 时包含的前后行数。
  - `global_threshold`：判断 segment 是否为求人块的全局阈值。
  - `field_threshold`：字段级标签（skill/contract 等）判定的参考阈值。
  - 正/负模板不再放在 `semantic_job_templates.json`，改由独立文件加载（`semantic_pos_templates.json` / `semantic_neg_templates.json`）。
  - `search`: 窗口搜索参数：
    - `negative_weight`
    - `length_penalty`
    - `window_max_lines`
    - `min_lines`
  - `fields`: `{ [field: string]: string[] }`，字段级模板列表（如 overview / work_content / skill / working_conditions / contract / restriction）。

## 处理流程
1. cleaner 后的正文通过 `LineFilter` 做轻量负向过滤（去问候、签名、免责声明等）。
2. 将过滤结果按行切分，移除空行。
3. 对每一行做 embedding，并使用前缀和快速构造任意连续窗口向量。
4. 对所有连续窗口（长度范围 `min_lines..window_max_lines`）计算分数：`window_score = max(sim(global)) - negative_weight * max(sim(negative)) - length_penalty * log(1+lines)`。
5. 选择分数最高窗口，若分数 >= `global_threshold`，输出 `SemanticResult`：
6. 选择分数最高窗口，若分数 >= `global_threshold`，输出 `SemanticResult`：
   - `text`: 覆盖行拼接后的正文
   - `score`: 最优窗口分数
   - `start_line` / `end_line`: 覆盖行区间（基于过滤后的行索引）
   - `matched`: 是否超过阈值
   - `line_scores`: 每行正负融合后的基础分数
6. 字段级模板会在内部计算各字段最大相似度，作为调试/扩展用，不影响当前返回结构。

## 日志
- info 级：body 总数、`global_threshold`、top window 分数示例。
- debug 级：各字段模板的最高相似度，便于阈值调试。

## 对外接口
- `SemanticExtractor.extract(body: str) -> SemanticResult`，对调用方保持兼容。
- `Config.semantic_global_templates()` / `Config.semantic_field_templates()`：访问模板；`Config.SEMANTIC_CONTEXT_RADIUS`、`Config.SEMANTIC_JOB_GLOBAL_THRESHOLD`、`Config.SEMANTIC_JOB_FIELD_THRESHOLD` 提供相关阈值。
