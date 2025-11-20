# 测试策略（规划）

- 现状：设计阶段暂未编写测试，用于占位。
- 单元测试：计划使用 pytest，按模块在 `tests/` 下镜像 `app/` 结构命名 `test_*.py`。
- 接口测试：优先采用 httpx/AsyncClient 直接调用 FastAPI 应用，覆盖健康检查与 Pipeline 关键路径。
- 覆盖率：功能落地后设定基础门槛（建议 ≥80% 针对新增代码），在 CI 中执行。
- 前端测试：React 落地后按需加入 Vitest/Testing Library，覆盖组件渲染与 API 调用。
