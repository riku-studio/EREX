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
      line-filter (轻量行过滤)
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
      (可选) PostgreSQL ←→ FastAPI → React 前端
```

说明：
- 管线输入为邮件（eml/msg/pst），各模块可按配置开启/关闭。
- 是否写入 PostgreSQL 取决于部署阶段需求，未启用时可直接返回结果给前端。
- Pipeline 适用于泛 NLU 提取任务，并非限定招聘场景。
