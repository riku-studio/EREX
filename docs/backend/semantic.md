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
    - `pos_top_k`（正向模板取 top-k 相似度均值）
    - `negative_weight`
    - `negative_power`
    - `length_penalty`
    - `length_reward`
    - `center_weight`
    - `cluster_delta`
    - `cluster_min_windows`
    - `cluster_overlap_only`
    - `trim_tail_neg_threshold`
    - `trim_tail_pos_threshold`
    - `trim_head_neg_threshold`
    - `trim_head_pos_threshold`
    - `boundary_neg_threshold`
    - `boundary_pos_threshold`
    - `boundary_tail_run`
    - `boundary_head_run`
    - `window_max_lines`
    - `min_lines`
  - `fields`: `{ [field: string]: string[] }`，字段级模板列表（如 overview / work_content / skill / working_conditions / contract / restriction）。

## 处理流程
1. cleaner 后的正文通过 `LineFilter` 做轻量负向过滤（去问候、签名、免责声明等）。
2. 将过滤结果按行切分，移除空行。
3. 对每一行做 embedding，并使用前缀和快速构造任意连续窗口向量。
4. 对所有连续窗口（长度范围 `min_lines..window_max_lines`）计算分数：  
   `window_score = mean(top-k sim(global)) - negative_weight * (max(sim(negative)) ^ negative_power) - length_penalty * log(1+lines) + length_reward * log(1+lines) + center_weight * center_score`
5. `center_score` 基于窗口中心与正文中心的距离，越靠近正文中部得分越高（0~1）。
6. 以最高分窗口为核心，收集 `score >= max(global_threshold, best_score - cluster_delta)` 的候选窗口；若候选数达到 `cluster_min_windows`，并在 `cluster_overlap_only=true` 下与核心窗口重叠，则合并成更完整边界。
7. 对合并后的边界做头尾裁剪：
   - 尾部：公司/签名/免责声明类负向行优先剔除；
   - 头部：问候类行轻度剔除；
   - 并结合行级正负分阈值（`trim_*`）抑制无关行。
8. 最终分数仍使用核心窗口最高分，输出 `SemanticResult`：
   - `text`: 覆盖行拼接后的正文
   - `score`: 最优窗口分数
   - `start_line` / `end_line`: 覆盖行区间（基于过滤后的行索引）
   - `matched`: 是否超过阈值
   - `line_scores`: 每行正负融合后的基础分数
6. 字段级模板会在内部计算各字段最大相似度，作为调试/扩展用，不影响当前返回结构。

## 已固化最佳规则/超参
- 规则：`mean_pos_max_neg`
  - 正向分数：`mean(top-3 sim(global_templates))`
  - 负向分数：`max(sim(negative_templates))`
- 默认超参（已写回配置）：
  - `global_threshold=0.15`
  - `search.pos_top_k=3`
  - `search.negative_weight=0.15`
  - `search.negative_power=1.4`
  - `search.length_penalty=0.0`
  - `search.length_reward=0.0`
  - `search.center_weight=0.0`
  - `search.min_lines=2`
  - `search.window_max_lines=44`
  - `search.cluster_delta=0.22`
  - `search.cluster_min_windows=6`
  - `search.cluster_overlap_only=true`
  - `search.trim_tail_neg_threshold=0.35`
  - `search.trim_tail_pos_threshold=0.34`
  - `search.trim_head_neg_threshold=0.55`
  - `search.trim_head_pos_threshold=0.3`
  - `search.boundary_neg_threshold=0.5`
  - `search.boundary_pos_threshold=0.32`
  - `search.boundary_tail_run=0`（默认关闭）
  - `search.boundary_head_run=0`（默认关闭）

## 本轮验证结果（`tests/out_recruitment_extract.csv`）
- 评估口径：`block_text` 上预测窗口 vs `recruitment_text` 金标窗口（行级）。
- 指标：
  - `line_precision=0.7630`
  - `line_recall=0.9740`
  - `line_f1=0.8557`
  - `exact_rate=0.1364`
  - `mean_iou=0.7444`

## 起止行差评估（你提出的新口径）
- 对每封邮件：
  - 在原文 `block_text` 中定位 `recruitment_text` 的 `(gold_start, gold_end)`；
  - 在原文 `block_text` 中定位 `semantic_text` 的 `(pred_start, pred_end)`；
  - 计算 `line_diff = |pred_start-gold_start| + |pred_end-gold_end|`。
- 全量目标：最小化 `total_line_diff = Σ line_diff`。
- 本轮最优（含增强负模板）：
  - `total_line_diff=794`（按当前 `semantic.py` 真实运行复评）
  - `avg_line_diff=5.1558`
  - `exact_match_rows=26/154`
  - `exact_rate=0.1688`
- 说明：行级边界 run 判定已实现为可选项，但在当前数据集开启后会过裁剪，`total_line_diff` 反而上升（实验最优约 `817`），因此默认关闭。

## 如何获取最优规则/超参
1. 构造 gold 标注：
   - 使用 `tests/out_split.csv` 的 `block_text`。
   - 使用 `tests/out_recruitment_extract.csv` 的 `recruitment_text` 作为目标片段（连续原文行）。
2. 运行离线调参脚本（位于 `backend/tests/tune_semantic_window_rules.py`）：
   - 该脚本会枚举规则和超参组合，计算 line-level Precision/Recall/F1、Exact Rate、Mean IoU。
3. 输出结果：
   - 全量对比：`tests/semantic_window_tuning_results.csv`
   - 最佳配置：`tests/semantic_window_tuning_best.json`
4. 选型策略：
  - 本轮以 `mean_iou` 为主目标，`exact_rate` 为次目标，兼顾 `line_f1`。
  - 在业务对召回更敏感时，可降低阈值；对精度更敏感时，提高 `negative_weight` 或降低 `length_reward`。

## 日志
- info 级：body 总数、`global_threshold`、top window 分数示例。
- debug 级：各字段模板的最高相似度，便于阈值调试。

## 对外接口
- `SemanticExtractor.extract(body: str) -> SemanticResult`，对调用方保持兼容。
- `Config.semantic_global_templates()` / `Config.semantic_field_templates()`：访问模板；`Config.SEMANTIC_CONTEXT_RADIUS`、`Config.SEMANTIC_JOB_GLOBAL_THRESHOLD`、`Config.SEMANTIC_JOB_FIELD_THRESHOLD` 提供相关阈值。
