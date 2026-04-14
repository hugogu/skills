---
name: gitlab-mr-review
description: |
  自动审查GitLab Merge Request并提供基于best practice的代码Review。
  当用户需要review GitLab MR、进行代码审查、检查代码质量时使用此skill。
  适用于需要自动化代码review流程、确保代码质量、维护代码一致性的场景。
  支持JavaScript/TypeScript、Java、Python代码的review。
  触发场景包括："review这个MR", "检查GitLab MR代码质量", "对这个PR进行代码审查",
  "帮我看看这个merge request", "自动review GitLab MR", "GitLab MR代码审查"等。
---

# GitLab MR Review Skill

## Overview

此skill用于自动化GitLab Merge Request的代码审查流程。它会：

1. 获取MR的变更内容（diff）、现有comments和元数据
2. 使用LLM直接分析diff，基于checklist和best practice发现代码问题
3. 过滤已有comments避免重复
4. 在MR上留下inline comments（针对具体代码行）
5. 发布带整体质量评级的review总结

## Prerequisites

- GitLab Personal Access Token（具有`api`权限）
- 环境变量 `GITLAB_TOKEN` 或技能执行时提供的token
- GitLab项目URL和MR IID（MR编号）

## Supported Languages

- JavaScript/TypeScript
- Java
- Python

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

从用户获取或从提供的 MR URL 中解析必需信息：

```
必需参数：
- gitlab_url: GitLab实例URL (e.g., https://gitlab.com)
- project_path: 项目路径 (e.g., "group/project-name")
- mr_iid: MR编号 (e.g., 42)
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
echo ".mr-review/" >> .gitignore
```

如果 `.gitignore` 中已存在则无需重复添加。

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

### Step 5: LLM Code Analysis

将以下信息提供给LLM进行分析：
- `changes.diff` 或 `changes.json` 中的代码变更
- `existing_comments.json` 中的现有评论
- checklist 内容

**分析要求**：

1. **只关注新增/修改的代码**（diff中以 `+` 开头的行）。
2. **行号必须准确**：`line` 必须是该代码在新文件中的实际行号（diff hunk中的新文件行号，即 `+` 行对应的行号），**不是** diff文件的物理行号。如果某行是新增文件中的第18行，就写18。
3. **避免重复评论**：如果 `existing_comments.json` 中已有相同文件、相近行号、相似描述的评论，不要再提。
4. **severity 分级**：
   - `critical`: 阻塞性问题（安全漏洞、明显bug、BLOCKER级问题）
   - `warning`: 需要关注（风格问题、潜在问题、不应提交的本地配置等）
   - `info`: 建议性意见（可以忽略）
5. **comment 格式**：每个comment必须包含以下字段：
   - `file_path`: 文件路径（如 `src/main/java/com/example/Foo.java`）
   - `line`: 新文件中的行号（整数）
   - `severity`: `critical` | `warning` | `info`
   - `type`: 问题类型，如 `security`, `logic`, `code_consistency`, `style`, `performance`
   - `message`: 问题描述（中文或英文，视项目语言而定）
   - `suggestion`: 改进建议（可选，使用GitLab suggestion格式时提供具体代码）
   - `reference`: 参考链接（可选）
   - `base_sha`, `head_sha`, `start_sha`: 从metadata中获取

**逻辑合理性分析（重点）**：
除编码规范外，必须重点审查以下逻辑问题：
- **分支完备性**：if/else/switch 是否覆盖所有场景，是否存在隐式遗漏
- **循环与终止**：循环是否有明确退出条件，是否会死循环或提前终止
- **状态一致性**：异常发生后对象/状态是否处于合理状态，是否留下半完成修改
- **并发与时序**：多线程/异步场景下是否存在竞态条件、死锁、时序错误
- **数值与边界**：除零、溢出、越界、浮点精度、时区处理是否正确
- **幂等性与副作用**：重复调用是否安全，深/浅拷贝是否导致意外副作用
- **条件判断陷阱**：短路求值误用、== 与 equals 混用、类型隐式转换

**查找有效行号的快捷方式**：
如果不知道某行精确的 `+` 行号，可以直接运行：

```bash
python3 skills/gitlab-mr-review/scripts/show_diff_lines.py \
  --changes-file .mr-review/mr_data_42/changes.json \
  --file "FooService.java" \
  --context 2
```

这会输出该文件所有可评论的 `+` 行及其前后 2 行上下文，直接复制行号即可。

**特别注意的常见陷阱**：
- `application.yml`、`.properties`、环境配置文件中出现的端口变更、超时变更、本地路径等，很可能是本地开发配置误提交，应标记为 `warning`。
- 注解冗余（如Java中同时使用 `@Service` 和 `@Component`）、注释残留调试标记、魔法数字、缺少泛型参数、使用 `System.out.println` 等。
- 捕获通用 `Exception` 在业务代码中常见，但如果不是必要的回退逻辑，可酌情标记为 `info` 或 `warning`。
- 如果 SonarQube 等工具已在现有comments中指出了某问题，不要再重复评论。

### Step 6: Generate Review Comments JSON

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
    "has_conflicts": false
  },
  "comments": [
    {
      "file_path": "src/main/java/com/example/Foo.java",
      "line": 18,
      "severity": "warning",
      "type": "code_consistency",
      "message": "同时使用了 @Service 和 @Component 注解，存在冗余",
      "suggestion": "移除 @Component 注解，保留 @Service 即可",
      "base_sha": "...",
      "head_sha": "...",
      "start_sha": "..."
    }
  ],
  "stats": {
    "total_issues": 1,
    "by_severity": {"critical": 0, "warning": 1, "info": 0},
    "by_type": {"code_consistency": 1}
  }
}
```

如果 MR 存在合并冲突，请在 `metadata.has_conflicts` 中标记为 `true`（用于在 Summary 中高亮）。

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
8. **使用LLM直接分析diff**（重点审查逻辑合理性），生成 `.mr-review/mr_42_comments.json`
9. **直接运行 CLI 命令** `validate_comments.py` 验证行号
10. **直接运行 CLI 命令** `post_comments.py --dry-run` 预览
11. 确认后正式发布inline comments和summary comment
12. 向用户报告review结果摘要

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
- **Code Consistency**: 2
- **Logic**: 1

### 需要关注的问题

🔴 `src/main/java/com/example/AuthController.java:23` - 用户输入未转义直接拼接到SQL查询
🟡 `src/main/java/com/example/Utils.java:45` - 函数超过50行，建议拆分

### 评审意见

当前代码存在 **1** 个 critical 问题，强烈建议修复后再合并。

### 建议行动

- [ ] **优先修复** critical 级别的问题
- [ ] 考虑修复 warning 级别的问题
- [ ] 酌情参考 info 级别的建议

---
*This review was generated automatically. Please feel free to discuss any suggestions.*
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

获取MR数据。建议统一输出到 `.mr-review/` 子目录。

```bash
python3 skills/gitlab-mr-review/scripts/fetch_mr.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --mr-iid 42 \
  --token $GITLAB_TOKEN \
  --output-dir .mr-review/mr-data
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

发布 comments 和 Summary 到 MR。支持 `--dry-run` 预览。

```bash
python3 skills/gitlab-mr-review/scripts/post_comments.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --mr-iid 42 \
  --token $GITLAB_TOKEN \
  --comments-file .mr-review/comments_validated.json \
  --metadata-file .mr-review/mr-data/metadata.json
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

### Authentication

所有API请求使用 `Private-Token` HTTP Header进行认证：

```
Private-Token: <your_access_token>
```

需要的Token权限：
- `api` - 访问GitLab API
- 项目访问权限（Developer或更高角色）
