# **技术栈（Tech Stack）**

| 层级       | 技术                                 |
| ---------- | ------------------------------------ |
| 后端框架   | FastAPI                              |
| 前端       | React (Vite / CRA)                   |
| 数据库     | PostgreSQL（Docker 部署）            |
| 邮件解析   | pypff, extract_msg, Python email     |
| NLP        | sentence-transformers (MiniLM-L6-v2) |
| 文本分块   | Regex + 配置驱动                     |
| 关键字抽取 | 定制 Trie + Regex                    |
| 分类模块   | 配置驱动多分类器                     |
| 配置       | YAML / JSON                          |
| 部署       | docker-compose                       |