# **架构设计（Architecture Design）**

## 1. 高层系统架构

```
               +----------------------------+
               |         Frontend (React)   |
               |   SPA, Charts, Tables      |
               +-------------+--------------+
                             |
                             | REST API (FastAPI)
                             |
               +-------------v--------------+
               |         Backend API        |
               |   FastAPI + PostgreSQL     |
               +-------------+--------------+
                             |
                   Core Extraction Pipeline
                             |
      +-------------------------------------------------------+
      |                       Core Modules                    |
      |  importer → cleaner → semantic → splitter → extractor |
      |  → classifier → aggregator → statistics               |
      +-------------------------------------------------------+
                             |
                   +---------v-------------+
                   |  PostgreSQL Database  |
                   +------------------------+
```

------

## 2. Pipeline 处理流程（可插拔）

EREX 的核心是一个 **Pipeline Orchestrator**，每一步都是独立模块，可开关：

```
email_import (可选格式: eml/msg/pst)
 → body_extractor
 → semantic_filter (模板可切换)
 → block_splitter (模板可切换)
 → keyword_extractor (可切换技能词典)
 → classifier (可切换外国籍规则)
 → aggregator
 → 结构化输出
```

每个模块都支持：

- `enabled`: true/false
- 通过配置文件加载规则
- 面向“招聘信息”只是一个特定配置，不是系统限制

------

## 3. PostgreSQL + Docker-compose 架构

```
docker-compose.yml
│
├── app (FastAPI)
├── db (PostgreSQL)
└── pgadmin (可选)
```

PostgreSQL 用于存储：

- 原始邮件索引
- 解析后的结构化职位数据
- 技能统计数据
- 用户自定义模板（未来可扩展）

------

## 4. 模块化架构（Plugin-like Modules）

```
/app/services/
   ├── importer/          # 格式解析（eml/msg/pst）
   ├── cleaner/           # 正文清洗
   ├── semantic/          # 语义筛选（MiniLM）
   ├── splitter/          # 通用分块模块（支持多职位、多段落）
   ├── extractor/         # 技能抽取（可换模板）
   ├── classifier/        # 条件分类（外国籍/合规/风险等）
   ├── aggregator/        # 汇聚各模块结果
   └── pipeline.py        # 管线 orchestrator
```

每个模块都接受：

```python
def run(text: str, config: dict) -> dict:
    ...
```

