# GitHub Issue 驱动本地 Codex

本仓库使用 GitHub self-hosted runner，把带有 `codex` 标签的 Issue 交给本机已登录的 Codex CLI。Codex 修改并验证代码后，工作流会创建独立分支和 Pull Request；它不会直接更新默认分支。

## 为什么使用 Codex CLI

这一版只需要一次非交互式编码任务，`codex exec` 已经覆盖读取仓库、修改文件、运行测试和输出摘要的需求：

- Codex CLI：适合当前的单任务 CI 自动化，依赖少，也能复用本机 Codex 登录。
- Codex SDK：适合后续需要自建队列、重试、并发、结构化事件或多轮任务状态时使用。
- Codex App Server：适合开发长期运行、支持流式交互和审批界面的 Codex 产品，不适合这个最小工作流。

OpenAI 也提供 [`openai/codex-action`](https://learn.chatgpt.com/docs/github-action)，它同样会在底层运行 `codex exec`，更适合 GitHub-hosted runner 和以 GitHub Secret 管理 API key 的方案。本仓库直接调用 CLI，是为了明确复用本机安装、登录状态和隔离策略。

## 工作流程

1. 用户创建描述清楚的 GitHub Issue。
2. 有标签权限的维护者审查内容，并添加 `codex` 标签。
3. GitHub 将任务派发给带有 `codex-local` 标签的 Linux self-hosted runner。
4. runner 执行 `scripts/run-codex-issue.sh`，由本地 `codex exec` 修改工作区并运行测试。
5. 工作流拒绝发布对 `.github/workflows`、`.github/actions`、`.gitmodules` 或 Codex 执行脚本本身的改动，也拒绝 Codex 自行创建提交。
6. 有代码改动时创建分支和 PR；没有改动时在 Issue 留下 Codex 的说明。

## 一次性配置

### 1. 准备专用执行账号

建议为 runner 使用专用的低权限操作系统账号。该账号必须能访问构建所需工具，但不应能读取个人 SSH 密钥、云凭据或无关目录。

在该账号下确认依赖：

```bash
codex --version
codex login status
git --version
gh --version
jq --version
uv --version
```

如果尚未登录 Codex，在该账号下执行 `codex login`。也可以使用单独的 API key 登录，但不要把 key 写进仓库或工作流文件。

### 2. 注册 self-hosted runner

进入仓库的 `Settings → Actions → Runners → New self-hosted runner`，按 GitHub 页面生成的命令安装和注册 runner。注册时增加自定义标签 `codex-local`，并将 runner 安装为后台服务。

工作流要求以下标签同时匹配：

```text
self-hosted, linux, codex-local
```

runner 服务必须由上一步登录 Codex 的同一操作系统账号运行，否则它无法访问该账号的 Codex 登录状态。

### 3. 创建触发标签

在 GitHub 仓库中创建名为 `codex` 的 Issue 标签。不要通过 Issue 模板自动给所有新 Issue 添加这个标签；它是维护者确认并批准本地执行的安全闸门。

### 4. 设置仓库保护

建议启用默认分支保护，要求 PR 审查和测试通过后才能合并。工作流只在 Codex 运行完毕后把短期 `GITHUB_TOKEN` 提供给发布步骤。执行脚本还会通过一个最小环境启动 Codex，仅保留登录和基础运行所需变量，避免把 GitHub Actions 的运行时变量传给模型可调用的进程。

## 使用方式

Issue 中至少写清楚：

- 当前行为与期望行为；
- 可复现步骤或输入样例；
- 验收条件；
- 明确不应修改的范围。

维护者确认 Issue 适合自动执行后添加 `codex` 标签。可在仓库的 Actions 页面查看实时日志，完成后检查自动创建的 PR。

如果任务失败，先移除再重新添加 `codex` 标签即可创建一次新的运行。每次运行使用不同分支名，不会覆盖上一次结果。

## 安全边界

- self-hosted runner 会在本机执行由 Issue 间接触发的代码，建议使用专用账号、专用工作目录，最好再置于虚拟机或容器中。
- 只有维护者审查并添加 `codex` 标签后才运行；不要让不可信机器人自动加此标签。
- Codex 使用 `workspace-write` sandbox 和自动审批审查，不使用 `danger-full-access` 或跳过 sandbox。
- Codex 进程使用经过清理的最小环境；GitHub 发布令牌仅在后续发布步骤中出现。
- Codex 被禁止修改自动化配置和执行脚本；脚本在发布前还会再次检查这些路径和当前提交。
- 自动 PR 仍需人工审查。不要为机器人开启绕过分支保护的权限。
- 若机器还存有生产凭据，即使 prompt 有禁止读取秘密的说明，也不应把提示词当成安全隔离；应通过操作系统账号、目录权限或容器真正隔离。

## 相关文件

- `.github/workflows/issue-to-local-codex.yml`：GitHub 事件、runner 和 PR 发布逻辑。
- `scripts/run-codex-issue.sh`：安全构造 prompt、调用本地 Codex、检查受保护路径。
