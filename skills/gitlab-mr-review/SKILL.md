---
name: gitlab-mr-review
description: |
  自动审查GitLab Merge Request或Commit并提供基于best practice的代码Review。
  当用户需要review GitLab MR/Commit、进行代码审查、检查代码质量时使用此skill。
  适用于需要自动化代码review流程、确保代码质量、维护代码一致性的场景。
  支持JavaScript/TypeScript、Java、Python代码的review。
  触发场景包括："review这个MR", "review这个commit", "检查GitLab MR代码质量", "对这个PR进行代码审查",
  "帮我看看这个merge request", "自动review GitLab MR", "GitLab MR代码审查", "review commit"等。
---

# GitLab MR Review Skill

## Overview

此skill用于自动化GitLab Merge Request和Commit的代码审查流程。它会：

1. 获取MR或Commit的变更内容（diff）、现有comments和元数据
2. 使用LLM直接分析diff，基于checklist和best practice发现代码问题
3. 过滤已有comments避免重复
4. 在MR或Commit上留下inline comments（针对具体代码行）
5. 发布带整体质量评级的review总结

## Prerequisites

- GitLab Personal Access Token（具有`api`权限）
- 环境变量 `GITLAB_TOKEN` 或技能执行时提供的token
- GitLab项目URL和MR IID（MR编号）或 Commit SHA

## Supported Languages

- JavaScript/TypeScript
- Java
- Python

## Review Philosophy

本 skill 的 AI Review 定位于**补充**而非**重复**现有静态代码分析工具（如 SonarQube、ESLint、Checkstyle、Pylint）。

### 不评论的内容（静态工具已覆盖）

- 命名规范（camelCase、PascalCase、snake_case 等）
- 代码格式（缩进、空格、分号、引号、行长度、括号位置）
- 简单 import 问题（未使用 import、通配符导入、排序）
- 方法/类长度（除非已经严重到影响设计合理性）
- 基础语法错误、拼写错误

### 重点评论的内容（AI 更擅长）

- **业务语义合理性**：代码变更在业务层面是否合理，逻辑是否符合业务常识，提示语是否准确
- **架构与设计**：职责划分、抽象层次、SOLID 原则、分层合理性、设计模式选择
- **逻辑正确性**：分支遗漏、边界条件、并发竞态、幂等性、状态一致性、异常恢复
- **业务安全**：越权、数据泄漏、动态 SQL/命令注入、路径遍历等需要上下文判断的问题
- **数据一致性**：事务边界、缓存一致性、并发写控制
- **可维护性与扩展性**：硬编码业务规则、重复逻辑、接口稳定性、新增功能的改动范围

## Checklist Configuration

Review checklist采用分层配置：

1. **内置标准checklist**: `references/checklist-{language}.md`
2. **项目自定义checklist**: 项目根目录下的 `.review-checklist.md`
3. **优先级**: 项目自定义 > 内置标准

项目可以通过创建 `.review-checklist.md` 来自定义review规则。

## Workflow

### Step 1: Gather Information

**⚠️ 重要：不要尝试直接通过网络请求（WebFetch / curl）访问 GitLab URL。**

许多 GitLab 实例位于内网或需要特殊认证，直接网络请求会失败（如 `Unable to verify if domain is safe to fetch`）。**正确的做法是：立即解析 URL 参数，然后使用本地的 `fetch_mr.py` 脚本配合 `GITLAB_TOKEN` 调用 GitLab API。**

从用户获取或从提供的 MR/Commit URL 中解析必需信息：

**MR Review 必需参数**：
```
- gitlab_url: GitLab实例URL (e.g., https://gitlab.com)
- project_path: 项目路径 (e.g., "group/project-name")
- mr_iid: MR编号 (e.g., 42)
- token: GitLab Personal Access Token（可选，优先使用GITLAB_TOKEN环境变量）
```

**Commit Review 必需参数**：
```
- gitlab_url: GitLab实例URL
- project_path: 项目路径
- commit_sha: Commit SHA (e.g., "a1b2c3d4...")
- token: GitLab Personal Access Token（可选，优先使用GITLAB_TOKEN环境变量）
```

检查token可用性（不要写wrapper脚本，直接用单行命令）：

```bash
python3 -c "import os; t=os.environ.get('GITLAB_TOKEN',''); print('yes' if t else 'no', len(t))"
```

如果token不可用，请用户先设置环境变量 `GITLAB_TOKEN` 或提供token。

### Step 2: Configure Output Directory

为了避免临时 review 文件污染项目目录，**统一使用 `.mr-review/` 作为输出目录**，并在项目 `.gitignore` 中忽略它：

```bash
grep -q ".mr-review/" .gitignore 2>/dev/null || echo ".mr-review/" >> .gitignore
```

### Step 3: Fetch MR Data

**不要写 Python wrapper，直接运行以下命令**（根据环境用 `python` 或 `python3`）：

```bash
python3 skills/gitlab-mr-review/scripts/fetch_mr.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --mr-iid 42 \
  --token "$GITLAB_TOKEN" \
  --output-dir .mr-review/mr_data_42
```

Windows PowerShell 示例：

```powershell
python skills/gitlab-mr-review/scripts/fetch_mr.py `
  --gitlab-url https://gitlab.com `
  --project group/project `
  --mr-iid 42 `
  --token $env:GITLAB_TOKEN `
  --output-dir .mr-review/mr_data_42
```

输出目录 `.mr-review/mr_data_42` 下会生成：
- `mr_data.json`: 合并数据（mr_info + changes + existing_comments + metadata）
- `mr_info.json`: MR基本信息
- `changes.json`: 变更文件列表及每个文件的diff
- `changes.diff`: 原始diff文本
- `existing_comments.json`: 现有的review comments
- `metadata.json`: 元数据（语言、SHA refs等）

读取 `metadata.json` 了解MR概况，读取 `changes.diff` 或 `changes.json` 分析代码变更。

### Step 4: Load Checklist

根据 `metadata.json` 中的 `detected_language` 加载对应checklist：

1. 先检查项目根目录是否有 `.review-checklist.md`
2. 如果没有，使用内置的 `references/checklist-{detected_language}.md`

使用Read工具读取checklist内容。

### Step 5: Round 1 — Business Rationality Review（默认执行）

**输入**：`changes.diff`（或 `changes.json`）、`existing_comments.json`

对变更进行第一轮分析，**只使用以下提示词**：

```
从业务功能实现合理性的角度进行分析
```

**本轮要求**：
- **抛开 checklist**，purely 从业务常识和工程直觉出发。
- 重点发现：**业务功能实现的合理性**。
- 先看文件名、类名、方法名推断业务场景，再判断代码中的常量、枚举、默认值、返回逻辑是否与该场景常识匹配。
- 本轮以 comment 列表形式暂存结果，不要输出最终 JSON。

**行号规则（通用）**：
- `line` 必须是 diff 中 `+` 行对应的新文件实际行号。
- **严禁手动推算、心算或数 diff hunk 来猜测行号**。diff 格式极易误导，手动计算会浪费大量时间且极易出错。
- **对任何不确定行号的 comment，必须在生成 JSON 前运行 `show_diff_lines.py` 获取精确行号**：
  ```bash
  python3 skills/gitlab-mr-review/scripts/show_diff_lines.py \
    --changes-file .mr-review/mr_data_42/changes.json \
    --file "FooService.java" \
    --context 0
  ```
- 直接复制脚本输出中的 `+ 行号`，不要自行加减。

---

### Step 6: Round 2 — Structured Review（仅在用户要求全面分析时执行）

**触发条件**：用户明确说了"全面分析"、"详细 review"、"深度检查"、"按 checklist review"等类似要求时，才执行本步骤。否则跳过。

**输入**：同样的 diff + Round 1 已发现的 comments + checklist 内容

在 Round 1 的基础上，用 checklist 作为灵感参考，补充检查架构、设计、逻辑、安全和数据一致性等方面。**禁止 checklist-driven scanning**。

**本轮要求**：
- 如果 Round 1 已经提到了某个问题，本轮不要再重复。
- 同样以 comment 列表形式暂存，不要输出最终 JSON。

---

### Step 6.5: Resolve Line Numbers (Before JSON)

在生成 JSON **之前**，**必须确保每个 comment 的行号都是准确的**。

如果你有任何一条 comment 的行号不是 100% 确定：

1. **运行 `show_diff_lines.py` 查看精确行号**：
   ```bash
   python3 skills/gitlab-mr-review/scripts/show_diff_lines.py \
     --changes-file .mr-review/mr_data_42/changes.json \
     --file "TradeFileUploadServiceImpl.java" \
     --context 0
   ```
2. 在输出中找到你要评论的那一行代码，**直接复制**前面的 `+ 行号`。
3. 更新你的 comment 列表中的 `line` 字段。

**禁止的行为**：
- ❌ 在脑中根据 diff hunk 的 `@@` 信息推算行号
- ❌ 手动数 diff 文件的物理行数然后加减
- ❌ 凭记忆或猜测填写行号

这是导致 review 发布 400 失败和浪费时间的主要原因，请务必使用脚本获取。

---

### Step 7: Generate Review Comments JSON

如果**只执行了 Round 1**（默认情况）：直接将 Round 1 的 comments 生成 JSON。

如果**执行了 Round 1 + Round 2**（用户要求全面分析时）：
1. 将两轮的 comments 合并到同一个列表。
2. **去重**：如果同一文件、同一行或相近行（±3 行）有相似描述的评论，只保留一条（优先保留描述更具体、severity 更高或带有 suggestion 的一条）。

**控制总量**：无论是一轮还是两轮，最终 comments 都建议控制在 **6-8 条**以内。优先保留 `critical` 和 `warning`，将低价值的 `info` 合并或删除。

确保每条 comment 都包含 `base_sha`、`head_sha`、`start_sha`（从 `metadata.json` 中获取）。

将合并后的结果保存为 JSON 文件：

`.mr-review/mr_42_comments.json`（MR 模式）或 `.mr-review/commit_a1b2c3d4_comments.json`（Commit 模式）

```json
{
  "metadata": {
    "gitlab_url": "...",
    "project_path": "...",
    "mr_iid": 42,
    "mr_title": "...",
    "detected_language": "java",
    "total_files": 5,
    "total_additions": 120,
    "total_deletions": 30,
    "has_conflicts": false,
    "model": "kimi-for-coding/k2p5",
    "token_usage": 15234
  },
  "comments": [
    {
      "file_path": "src/main/java/com/example/FooService.java",
      "line": 42,
      "severity": "warning",
      "type": "business_semantics",
      "message": "硬编码值与当前业务场景的常识不符，建议根据实际业务规则进行配置化或选择合适的枚举",
      "suggestion": "将硬编码的业务参数抽为配置项或根据类型动态选择",
      "base_sha": "...",
      "head_sha": "...",
      "start_sha": "..."
    }
  ],
  "stats": {
    "total_issues": 1,
    "by_severity": {"critical": 0, "warning": 1, "info": 0},
    "by_type": {"business_semantics": 1}
  }
}
```

如果 MR 存在合并冲突，请在 `metadata.has_conflicts` 中标记为 `true`（用于在 Summary 中高亮）。

**模型与 Token 信息**：在 `metadata` 中记录本次 review 使用的模型名称和整体 Token 消耗量：
- `model`: 当前使用的模型名称（如 `kimi-for-coding/k2p5`）
- `token_usage`: 本次 review 整体消耗的 Token 总量（整数）

**不要自己写 Python 脚本来保存 JSON**，直接使用 `Write` 工具写入文件即可。

### Step 8: Validate Line Numbers (MUST DO)

将LLM分析结果整理为如下JSON结构，并保存到文件 `.mr-review/mr_42_comments.json`：

```json
{
  "metadata": {
    "gitlab_url": "...",
    "project_path": "...",
    "mr_iid": 42,
    "mr_title": "...",
    "detected_language": "java",
    "total_files": 5,
    "total_additions": 120,
    "total_deletions": 30,
    "has_conflicts": false,
    "model": "kimi-for-coding/k2p5",
    "token_usage": 15234
  },
  "comments": [
    {
      "file_path": "src/main/java/com/example/FooService.java",
      "line": 42,
      "severity": "warning",
      "type": "business_semantics",
      "message": "硬编码值与当前业务场景的常识不符，建议根据实际业务规则进行配置化或选择合适的枚举",
      "suggestion": "将硬编码的业务参数抽为配置项或根据类型动态选择",
      "base_sha": "...",
      "head_sha": "...",
      "start_sha": "..."
    }
  ],
  "stats": {
    "total_issues": 1,
    "by_severity": {"critical": 0, "warning": 1, "info": 0},
    "by_type": {"business_semantics": 1}
  }
}
```

如果 MR 存在合并冲突，请在 `metadata.has_conflicts` 中标记为 `true`（用于在 Summary 中高亮）。

**模型与 Token 信息**：在 `metadata` 中记录本次 review 使用的模型名称和整体 Token 消耗量：
- `model`: 当前使用的模型名称（如 `kimi-for-coding/k2p5`）
- `token_usage`: 本次 review 整体消耗的 Token 总量（整数）

**不要自己写 Python 脚本来保存 JSON**，直接使用 `Write` 工具写入文件即可。

### Step 7: Validate Line Numbers (MUST DO)

**发布前必须验证行号**，否则极有可能因为行号不在有效 diff 范围内而 400 失败。直接运行：

```bash
python3 skills/gitlab-mr-review/scripts/validate_comments.py \
  --changes-file .mr-review/mr_data_42/changes.json \
  --comments-file .mr-review/mr_42_comments.json \
  --output .mr-review/mr_42_comments_validated.json
```

如果验证通过，会输出 `Validated: X/Y comments valid`。
如果存在无效行号，脚本会打印具体问题和最近的有效行号建议。你可以：
- 手动修正 JSON 中的行号后重新验证；或
- 加上 `--auto-fix` 参数让脚本自动调整到最近的有效行号（可能会偏离原意，谨慎使用）。

### Step 8: Post Review Comments

**先 `--dry-run` 预览**（强烈建议）：

```bash
python3 skills/gitlab-mr-review/scripts/post_comments.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --mr-iid 42 \
  --token "$GITLAB_TOKEN" \
  --comments-file .mr-review/mr_42_comments_validated.json \
  --metadata-file .mr-review/mr_data_42/metadata.json \
  --dry-run
```

确认无误后，正式发布：

```bash
python3 skills/gitlab-mr-review/scripts/post_comments.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --mr-iid 42 \
  --token "$GITLAB_TOKEN" \
  --comments-file .mr-review/mr_42_comments_validated.json \
  --metadata-file .mr-review/mr_data_42/metadata.json
```

`post_comments.py` 会自动跳过无法发布的行（如行号错误），并继续发布其余评论和 Summary。

### Commit Review Workflow

Commit Review 与 MR Review 流程基本一致，区别在于使用 `--commit-sha` 代替 `--mr-iid`，且输出目录建议以 commit SHA 命名：

**Step 1: Fetch Commit Data**

```bash
python3 skills/gitlab-mr-review/scripts/fetch_mr.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --commit-sha a1b2c3d4 \
  --token "$GITLAB_TOKEN" \
  --output-dir .mr-review/commit_data_a1b2c3d4
```

这会生成与 MR 模式兼容的输出文件（`changes.json`、`changes.diff`、`existing_comments.json`、`metadata.json` 等），以及额外的 `commit_info.json` 和 `commit_data.json`。

> 注意：Commit diff API 通常不会返回准确的 `additions`/`deletions` 统计，脚本会自动从 diff 文本中重新计算。

**Step 2-7**: 与 MR Review 相同（读取 checklist、Round 1 业务合理性分析、可选 Round 2 结构化分析、生成 JSON 评论、验证行号）。生成评论 JSON 时保存到 `.mr-review/commit_a1b2c3d4_comments.json`。

**Step 8: Post Commit Review Comments**

```bash
python3 skills/gitlab-mr-review/scripts/post_comments.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --commit-sha a1b2c3d4 \
  --token "$GITLAB_TOKEN" \
  --comments-file .mr-review/commit_a1b2c3d4_comments_validated.json \
  --metadata-file .mr-review/commit_data_a1b2c3d4/metadata.json \
  --dry-run
```

确认后正式发布（去掉 `--dry-run`）。评论会以 **Discussions** 的形式出现在该 Commit 的页面上。

### Step 9: Cleanup Temporary Files

Review 完成后，**默认清理**本次运行产生的 `.mr-review/` 临时数据，避免文件堆积：

```bash
rm -rf .mr-review/
```

如果用户明确要求保留中间文件用于排查，可以跳过此步骤。

## Comment Format

### Inline Comment Structure

```markdown
{emoji} **{SEVERITY}**: {Issue Type}

{description}

**建议**:
```suggestion
{suggested_code}
```

**参考**: {reference_link}
```

### Severity Levels

- **critical**: 阻塞性问题（安全漏洞、明显bug）
- **warning**: 需要关注（风格问题、潜在问题）
- **info**: 建议性意见（可以忽略）

## Avoiding Duplicate Comments

在LLM分析前，将现有comments提供给LLM：

1. **相同位置**: 检查相同文件+行号是否有相同类型的comment
2. **相同内容**: 检查描述相似度 > 80%
3. **Resolved状态**: 已解决的问题不再重复comment
4. **变更检测**: 如果代码行已变更，可以重新comment

## Example Usage

### 用户请求

```
帮我review一下GitLab上的这个MR：https://gitlab.com/mygroup/myproject/-/merge_requests/42
```

### 执行流程

1. 解析MR URL，提取项目路径和MR IID
2. 检查环境变量 `GITLAB_TOKEN`
3. 如果没有token，询问用户提供
4. 确保 `.gitignore` 中忽略了 `.mr-review/`
5. **直接运行 CLI 命令** `fetch_mr.py` 获取MR数据到 `.mr-review/mr_data_42`
6. 读取 `metadata.json` 和 `changes.diff`
7. 检测编程语言，读取对应checklist
8. **Round 1（默认）**：只用提示词 *"从业务功能实现的合理性分析。"* 进行业务合理性分析
9. **Round 2（仅在用户要求全面分析时执行）**：使用完整 checklist 进行结构化分析
10. **对不确定的行号**，运行 `show_diff_lines.py` 获取精确行号
11. 合并结果（或直接使用 Round 1 结果），生成 `.mr-review/mr_42_comments.json`
12. **直接运行 CLI 命令** `validate_comments.py` 验证行号
13. **直接运行 CLI 命令** `post_comments.py --dry-run` 预览
14. 确认后正式发布inline comments和summary comment
15. 向用户报告review结果摘要
16. **清理 `.mr-review/` 临时文件**

### Commit Review 示例

**用户请求**：
```
帮我review一下这个commit：https://gitlab.com/mygroup/myproject/-/commit/a1b2c3d4
```

**执行流程**：
1. 解析Commit URL，提取项目路径和Commit SHA (`a1b2c3d4`)
2. 检查环境变量 `GITLAB_TOKEN`
3. **直接运行 CLI 命令** `fetch_mr.py --commit-sha a1b2c3d4` 获取数据到 `.mr-review/commit_data_a1b2c3d4`
4. 后续步骤（读取 checklist、Round 1 业务合理性分析、可选 Round 2 结构化分析、生成 JSON、验证行号、dry-run、发布）与 MR Review 完全一致
5. 向用户报告review结果摘要
6. **清理 `.mr-review/` 临时文件**

### 输出示例

**Summary Comment**:

```markdown
## 📝 MR Review Summary

**Reviewed**: feat: add user authentication (java)
**Files Changed**: 5 | **Additions**: 120 | **Deletions**: 30

### 整体质量评级: 🟡 C (Fair)

### 发现的问题

| Severity | Count |
|----------|-------|
| 🔴 Critical | 1 |
| 🟡 Warning | 3 |
| 🔵 Info | 2 |
| **Total** | **6** |

### 问题类别

- **Security**: 1
- **Logic**: 2
- **Architecture**: 1

### 需要关注的问题

🔴 `src/main/java/com/example/AuthController.java:23` - 存在安全风险，用户输入未做充分校验即参与敏感操作
🟡 `src/main/java/com/example/OrderService.java:67` - 并发场景下状态变更缺乏保护，可能出现数据不一致

### 评审意见

当前代码存在 **1** 个 critical 问题，强烈建议修复后再合并。

### 建议行动

- [ ] **优先修复** critical 级别的问题
- [ ] 考虑修复 warning 级别的问题
- [ ] 酌情参考 info 级别的建议

---
*This review was generated automatically. Reviewed by kimi-for-coding/k2p5. Total tokens: 15234. Please feel free to discuss any suggestions.*
```

## Error Handling

### Common Errors

- **401 Unauthorized**: Token无效或权限不足
- **404 Not Found**: MR不存在或已删除
- **403 Forbidden**: 没有review权限
- **API Rate Limit**: 遇到rate limit时等待并重试
- **400 Bad request - line_code can't be blank**: 行号不在有效diff范围内。已通过 `validate_comments.py` 前置校验基本规避；若仍发生，`post_comments.py` 会自动跳过并继续。

### Recovery

- Token问题：提示用户检查token权限
- MR不存在：确认MR编号和项目路径
- 权限问题：建议用户检查项目成员权限
- Rate limit：显示等待时间，稍后重试
- 行号问题：运行 `show_diff_lines.py` 查看精确行号，修正后重新验证

### Command Failure Handling（重要）

**禁止因为某个 CLI 命令失败就终止整个 review 任务。** 当脚本返回非 0 exit code 或抛出异常时，必须：

1. **读取 stdout + stderr 分析原因**
2. **根据错误类型采取对应措施**：

| 失败场景 | 处理策略 |
|---------|---------|
| `fetch_mr.py` 失败（401/403/404） | 向用户解释原因，请求确认 token/URL/权限，然后重试 |
| `fetch_mr.py` 失败（网络超时） | 等待 3-5 秒后重试一次；若仍失败，向用户说明网络问题 |
| `fetch_mr.py` 失败（Commit 不存在） | 确认 Commit SHA 是否完整正确（GitLab API 通常只需要前 8 位，但建议用完整 SHA） |
| `show_diff_lines.py` 失败 | 该脚本为辅助工具，失败不影响主流程。可直接读取 `changes.json` 手动分析 |
| `validate_comments.py` 失败（存在无效行号） | **必须**修正 JSON 中的行号（或换用 `--auto-fix`），然后重新验证，直到通过 |
| `post_comments.py` 失败（summary 或部分 inline 失败） | 分析日志：如果是单条 400 被跳过，其余成功，则任务已完成；如果是批量 401/403，向用户说明 |

3. **重试规范**：
   - 网络类错误（timeout、connection reset）可自动重试 **1 次**
   - 权限/配置类错误（401、403、MR 不存在）不要盲重试，先与用户确认
   - 行号类错误不要重试，必须修正数据

4. **何时可以停止**：
   - 只有 **token 完全不可用且用户无法提供**、或 **MR 确实不存在**、或 **网络完全不可达** 时，才向用户说明情况并停止后续步骤
   - 其他任何情况（包括部分评论发布失败）都应继续或恢复执行

## Best Practices

1. **增量Review**: 只评论新增或修改的代码
2. **建设性反馈**: 提供具体改进建议，不只是指出问题
3. **Context Awareness**: 考虑代码的上下文和业务逻辑
4. **Language Specific**: 遵循各语言的community standards
5. **Team Conventions**: 尊重团队已有的代码风格约定
6. **禁止写wrapper**: 所有操作通过现成的 CLI 脚本直接完成

## Scripts Reference

### fetch_mr.py

获取MR或Commit数据。建议统一输出到 `.mr-review/` 子目录。

**MR 模式**：
```bash
python3 skills/gitlab-mr-review/scripts/fetch_mr.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --mr-iid 42 \
  --token $GITLAB_TOKEN \
  --output-dir .mr-review/mr-data
```

**Commit 模式**：
```bash
python3 skills/gitlab-mr-review/scripts/fetch_mr.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --commit-sha a1b2c3d4 \
  --token $GITLAB_TOKEN \
  --output-dir .mr-review/commit-data
```

### show_diff_lines.py

显示每个文件所有可用于 inline comment 的 `+` 行及行号，支持按文件名过滤和上下文行数。

```bash
python3 skills/gitlab-mr-review/scripts/show_diff_lines.py \
  --changes-file .mr-review/mr-data/changes.json \
  --file "FooService.java" \
  --context 2
```

### validate_comments.py

发布前校验：检查每个 comment 的 `line` 是否对应 diff 中的有效 `+` 行。输出过滤后的 JSON。

```bash
python3 skills/gitlab-mr-review/scripts/validate_comments.py \
  --changes-file .mr-review/mr-data/changes.json \
  --comments-file .mr-review/comments.json \
  --output .mr-review/comments_validated.json
```

加 `--auto-fix` 可自动对齐到最近的有效行号。

### post_comments.py

发布 comments 和 Summary 到 MR 或 Commit。支持 `--dry-run` 预览。

**MR 模式**：
```bash
python3 skills/gitlab-mr-review/scripts/post_comments.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --mr-iid 42 \
  --token $GITLAB_TOKEN \
  --comments-file .mr-review/comments_validated.json \
  --metadata-file .mr-review/mr-data/metadata.json
```

**Commit 模式**：
```bash
python3 skills/gitlab-mr-review/scripts/post_comments.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --commit-sha a1b2c3d4 \
  --token $GITLAB_TOKEN \
  --comments-file .mr-review/comments_validated.json \
  --metadata-file .mr-review/commit-data/metadata.json
```

## GitLab API Reference

本Skill使用以下GitLab REST API端点：

### Merge Requests API

- **Get single MR**: `GET /projects/:id/merge_requests/:merge_request_iid`
  - 文档: https://docs.gitlab.com/api/merge_requests/#get-single-mr
  - 获取MR基本信息，包括diff_refs（base_sha, head_sha, start_sha）

- **List MR diffs**: `GET /projects/:id/merge_requests/:merge_request_iid/diffs`
  - 文档: https://docs.gitlab.com/api/merge_requests/#list-merge-request-diffs
  - 获取MR的diff内容

### Discussions API

- **List MR discussions**: `GET /projects/:id/merge_requests/:merge_request_iid/discussions`
  - 文档: https://docs.gitlab.com/api/discussions/#list-all-merge-request-discussion-items
  - 获取现有comments，用于避免重复

- **Create MR discussion**: `POST /projects/:id/merge_requests/:merge_request_iid/discussions`
  - 文档: https://docs.gitlab.com/api/discussions/#create-a-merge-request-thread
  - 创建inline comments（需要position参数）
  - Position参数必须包含：
    - `base_sha`: 目标分支的base commit SHA
    - `head_sha`: MR的head commit SHA
    - `start_sha`: 起始commit SHA（通常等于base_sha）
    - `position_type`: "text"（用于代码）
    - `new_path`: 文件路径
    - `old_path`: 文件路径
    - `new_line`: 行号（必须是diff中新增/修改行的有效行号）

### Notes API

- **Create MR note**: `POST /projects/:id/merge_requests/:merge_request_iid/notes`
  - 文档: https://docs.gitlab.com/api/notes/#create-a-merge-request-note
  - 发布general comments（非inline的summary评论）

### Commits API

- **Get a single commit**: `GET /projects/:id/repository/commits/:sha`
  - 文档: https://docs.gitlab.com/api/commits/#get-a-single-commit
  - 获取Commit基本信息，包括 `parent_ids`（用于构造 `base_sha`）

- **Get commit diff**: `GET /projects/:id/repository/commits/:sha/diff`
  - 文档: https://docs.gitlab.com/api/commits/#get-the-diff-of-a-commit
  - 获取Commit的diff内容（注意：此API返回的 `additions`/`deletions` 统计经常为0，脚本会自行从diff文本重算）

### Commit Discussions API

- **List commit discussions**: `GET /projects/:id/repository/commits/:sha/discussions`
  - 文档: https://docs.gitlab.com/api/discussions/#list-all-commit-discussion-items
  - 获取Commit现有的comments，用于避免重复

- **Create commit discussion**: `POST /projects/:id/repository/commits/:sha/discussions`
  - 文档: https://docs.gitlab.com/api/discussions/#create-a-commit-thread
  - 在Commit页面创建inline comments或general discussion（不带 `position` 时）
  - Position参数与MR discussion一致，其中 `head_sha` 为该commit本身，`base_sha`/`start_sha` 为其第一个parent commit

### Authentication

所有API请求使用 `Private-Token` HTTP Header进行认证：

```
Private-Token: <your_access_token>
```

需要的Token权限：
- `api` - 访问GitLab API
- 项目访问权限（Developer或更高角色）
