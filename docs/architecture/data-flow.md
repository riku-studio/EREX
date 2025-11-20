# **数据流（Data Flow）**

```
     +--------------+
     |  邮件文件    |
     +------+-------+
            |
            v
      importer (格式解析)
            |
            v
      cleaner (正文清洗)
            |
            v
      semantic (基于模板筛选)
            |
            v
      splitter (多块识别)
            |
            v
      extractor (关键字抽取)
            |
            v
      classifier (条件分类)
            |
            v
      aggregator (统一结构化)
            |
            v
      PostgreSQL ←→ FastAPI → React 前端
```

与“是否招聘”无关，该 Pipeline 可适用于任何 NLU 提取任务。