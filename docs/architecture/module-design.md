# **模块设计（Module Breakdown）**

此设计体现可扩展性：任意模块都可用于“招聘领域以外的用途”。

------

## 1. importer（邮件导入模块）

### 功能（通用化）

- 支持 EML / MSG / PST
- 返回统一结构体（不局限于招聘）

### 输出结构：

```json
{
  "id": "...",
  "subject": "...",
  "body_raw": "...",
  "from": "...",
  "date": "..."
}
```

------

## 2. cleaner（正文清洗模块）

### 功能（通用）

- 去 HTML 标签
- 清理引用
- 移除签名
- 标准化换行

### 输出：

```
body_clean
```

适用于任何领域，而非仅招聘解析。

------

## 3. semantic（通用语义筛选）

### 功能

- 基于模板（config/templates/*.json）
- 准确筛选与模板主题相关的句子

### 示例模板：

```
/config/templates/recruitment.json
/config/templates/foreigner.json
/config/templates/legal.json
```

用户可自定义：

```json
{
  "name": "recruitment",
  "template": [
    "求人情報", "募集要項", "必須スキル", "開発経験"
  ]
}
```

------

## 4. splitter（通用分块识别）

### 功能

对文本按自定义规则切割成多个“块”

适用于：

- 多职位识别
- 多条合同条款识别
- 多段客户投诉识别

### 通过配置驱动：

```
/config/patterns/recruitment_split.json
/config/patterns/legal_split.json
```

规则格式：

```json
{
  "patterns": [
    "(?=【[^】]+】)",
    "(?=■案件)",
    "(?=◆案件)"
  ]
}
```

------

## 5. extractor（通用关键字抽取）

不仅用于“技能抽取”，也可用于：

- 合同期条款抽取
- 风险关键词抽取
- 财务关键词抽取

关键字字典：

```
config/keywords/skills.json
config/keywords/legal_risk.json
config/keywords/complaint.json
```

技能例子：

```json
{
  "keywords": ["Java", "C++", "Python", "AWS", ...]
}
```

模块自动做长度排序，避免误匹配。

------

## 6. classifier（通用分类模块）

不仅用于“外国籍可/不可”，也可以扩展成：

- 合规/不合规
- 风险/安全
- 是否需要在留資格
- 是否是紧急案件
- 是否 NDA 限制

通过配置文件定义规则：

```
/config/classifiers/foreigner.json
/config/classifiers/legal_risk.json
```

样例：

```json
{
  "classes": {
    "ok": ["外国籍可", "国籍不問"],
    "ng": ["外国籍不可", "外国籍NG", "日本国籍のみ"],
    "unknown": []
  }
}
```

------

## 7. aggregator（聚合模块）

将多个模块输出合并为结构化结果：

```json
{
  "blocks": [
    {
      "text": "...",
      "semantic_hits": [...],
      "keywords": [...],
      "classify_result": "...",
      "stats": {...}
    }
  ]
}
```

适用于任何模板类型的抽取。

------

## 8. pipeline（核心 orchestrator）

配置化：

```json
{
  "pipeline": [
    "cleaner",
    "semantic",
    "splitter",
    "extractor",
    "classifier",
    "aggregator"
  ]
}
```

用户可以关闭/添加步骤：

```
pipeline.remove("classifier")
pipeline.add("custom_module")
```