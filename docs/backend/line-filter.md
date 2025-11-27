# Line Filter（轻量行过滤）

## 模块位置
- 路径：`app/services/preprocess/line_filter.py`
- 用法：`LineFilter.filter_lines(lines)` 接受 cleaner 产出的行列表，返回保留下来的行；配置全部从 `Config` 读取，可通过 `Config.ENABLE_LINE_FILTER` 快速开关。

## 规则类别
- 装饰线 / 分隔线：整行仅由 `LINE_FILTER_DECORATION_CHARS` 组成，或同一符号重复 3 次以上。
- 问候/结尾套话：匹配 `LINE_FILTER_GREETING_PATTERNS` 与 `LINE_FILTER_CLOSING_PATTERNS` 的正则。
- 签名/联系方式/公司信息：邮箱、URL、电话格式，或命中 `LINE_FILTER_SIGNATURE_KEYWORDS`，或以 `LINE_FILTER_SIGNATURE_COMPANY_PREFIX` 开头。
- 免责声明/配信停止/FAQ：匹配 `LINE_FILTER_FOOTER_PATTERNS` 的正则。
- 空行/纯符号行：去空白后为空，或极短且仅由标点/数字/符号组成。
- 防护策略：只要包含 `LINE_FILTER_JOB_KEYWORDS` 中的招聘关键词，一律保留，不触发上述删除。

## 配置项（`app/utils/config.py`）
- `ENABLE_LINE_FILTER`: 是否启用轻量过滤。
- `LINE_FILTER_CONFIG_PATH`: 配置文件路径，默认 `backend/config/line_filter.json`。
- `LINE_FILTER_DECORATION_CHARS`: 视为装饰的字符集合。
- `LINE_FILTER_GREETING_PATTERNS` / `LINE_FILTER_CLOSING_PATTERNS`: 问候与结尾的正则模式。
- `LINE_FILTER_SIGNATURE_COMPANY_PREFIX`: 判定为公司抬头的前缀列表。
- `LINE_FILTER_SIGNATURE_KEYWORDS`: 电话/邮箱等签名关键词。
- `LINE_FILTER_FOOTER_PATTERNS`: 免责声明、配信停止、FAQ 等脚注文案的正则。
- `LINE_FILTER_JOB_KEYWORDS`: 招聘相关关键词；命中即跳过删除。

## 与 semantic 的关系
- 作为 semantic 前的粗筛，不做语义判断，只过滤“肯定无用”的行，减少 embedding 的行数。
- 过滤后再拼回字符串传给 `SemanticExtractor.extract`，外部 API 不变，利于 A/B 测试与参数调优。
