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
5. 发布整体review总结

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

从用户获取必需信息：

```
必需参数：
- gitlab_url: GitLab实例URL (e.g., https://gitlab.com)
- project_path: 项目路径 (e.g., "group/project-name")
- mr_iid: MR编号 (e.g., 42)
- token: GitLab Personal Access Token（可选，优先使用GITLAB_TOKEN环境变量）
```

检查token可用性（使用Python，跨平台）：

```python
import os
token = os.environ.get("GITLAB_TOKEN", "")
print(f"Token available: {'yes' if token else 'no'}")
print(f"Token length: {len(token)}")
```

如果token不可用，请用户先设置环境变量 `GITLAB_TOKEN` 或提供token。

### Step 2: Fetch MR Data

使用Python脚本获取MR数据。此方式跨平台（Windows/macOS/Linux）：

```python
import os
import re
import subprocess
import sys
import tempfile

gitlab_url = "<用户提供的gitlab_url>"
project_path = "<用户提供的project_path>"
mr_iid = <用户提供的mr_iid>
token = os.environ.get("GITLAB_TOKEN", "<用户提供的token>")

output_dir = tempfile.mkdtemp(prefix="mr_review_")
script_path = os.path.join("skills", "gitlab-mr-review", "scripts", "fetch_mr.py")

result = subprocess.run(
    [
        sys.executable, script_path,
        "--gitlab-url", gitlab_url,
        "--project", project_path,
        "--mr-iid", str(mr_iid),
        "--token", token,
        "--output-dir", output_dir,
    ],
    capture_output=True,
    text=True,
)

print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

if result.returncode != 0:
    print("Failed to fetch MR data", file=sys.stderr)
    sys.exit(1)

match = re.search(r"OUTPUT_DIR:\s*(.+)", result.stdout)
fetched_dir = match.group(1).strip() if match else output_dir
print(f"Data directory: {fetched_dir}")
```

这会生成以下文件（均在 `fetched_dir` 中）：
- `mr_data.json`: 合并数据（mr_info + changes + existing_comments + metadata）
- `mr_info.json`: MR基本信息
- `changes.json`: 变更文件列表及每个文件的diff
- `changes.diff`: 原始diff文本
- `existing_comments.json`: 现有的review comments
- `metadata.json`: 元数据（语言、SHA refs等）

读取 `metadata.json` 了解MR概况，读取 `changes.diff` 或 `changes.json` 分析代码变更。

### Step 3: Load Checklist

根据 `metadata.json` 中的 `detected_language` 加载对应checklist：

1. 先检查项目根目录是否有 `.review-checklist.md`
2. 如果没有，使用内置的 `references/checklist-{detected_language}.md`

使用Read工具读取checklist内容。

### Step 4: LLM Code Analysis

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

**特别注意的常见陷阱**：
- `application.yml`、`.properties`、环境配置文件中出现的端口变更、超时变更、本地路径等，很可能是本地开发配置误提交，应标记为 `warning`。
- 注解冗余（如Java中同时使用 `@Service` 和 `@Component`）、注释残留调试标记、魔法数字、缺少泛型参数、使用 `System.out.println` 等。
- 捕获通用 `Exception` 在业务代码中常见，但如果不是必要的回退逻辑，可酌情标记为 `info` 或 `warning`。
- 如果 SonarQube 等工具已在现有comments中指出了某问题，不要再重复评论。

### Step 5: Generate Review Comments JSON

将LLM分析结果整理为如下JSON结构，并保存到文件：

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
    "total_deletions": 30
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
    "by_severity": {
      "critical": 0,
      "warning": 1,
      "info": 0
    },
    "by_type": {
      "code_consistency": 1
    }
  }
}
```

使用Python保存JSON：

```python
import json
import os
import tempfile

comments_file = os.path.join(tempfile.gettempdir(), f"mr_{mr_iid}_comments.json")
with open(comments_file, "w", encoding="utf-8") as f:
    json.dump(review_data, f, indent=2, ensure_ascii=False)

print(f"Comments saved to: {comments_file}")
```

### Step 6: Post Review Comments

先使用 `--dry-run` 预览：

```python
import os
import subprocess
import sys

script_path = os.path.join("skills", "gitlab-mr-review", "scripts", "post_comments.py")
subprocess.run([
    sys.executable, script_path,
    "--gitlab-url", gitlab_url,
    "--project", project_path,
    "--mr-iid", str(mr_iid),
    "--token", token,
    "--comments-file", comments_file,
    "--metadata-file", os.path.join(fetched_dir, "metadata.json"),
    "--dry-run",
])
```

确认无误后，正式发布：

```python
import os
import subprocess
import sys

script_path = os.path.join("skills", "gitlab-mr-review", "scripts", "post_comments.py")
result = subprocess.run([
    sys.executable, script_path,
    "--gitlab-url", gitlab_url,
    "--project", project_path,
    "--mr-iid", str(mr_iid),
    "--token", token,
    "--comments-file", comments_file,
    "--metadata-file", os.path.join(fetched_dir, "metadata.json"),
])

if result.returncode == 0:
    print("Review posted successfully")
else:
    print("Some comments may have failed to post", file=sys.stderr)
```

`post_comments.py` 会自动处理单条comment失败的情况（如行号不在有效diff范围内时会跳过并继续发布其余评论）。

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
2. 检查环境变量 `GITLAB_TOKEN`（使用Python脚本，跨平台）
3. 如果没有token，询问用户提供
4. 运行 `fetch_mr.py` 获取MR数据到一个临时目录
5. 读取 `metadata.json` 和 `changes.diff`
6. 检测编程语言，读取对应checklist
7. **使用LLM直接分析diff**，生成review comments JSON
8. 运行 `post_comments.py --dry-run` 预览
9. 确认后发布inline comments和summary comment
10. 向用户报告review结果摘要

### 输出示例

**Summary Comment**:

```markdown
## 📝 MR Review Summary

**Reviewed**: feat: add user authentication (java)
**Files Changed**: 5 | **Additions**: 120 | **Deletions**: 30

### 发现的问题

| Severity | Count |
|----------|-------|
| 🔴 Critical | 1 |
| 🟡 Warning | 3 |
| 🔵 Info | 2 |

### 问题类别

- **Security**: 1
- **Code Consistency**: 2
- **Logic**: 1

### 需要关注的问题

🔴 `src/main/java/com/example/AuthController.java:23` - 用户输入未转义直接拼接到SQL查询
🟡 `src/main/java/com/example/Utils.java:45` - 函数超过50行，建议拆分

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
- **400 Bad request - line_code can't be blank**: 行号不在有效diff范围内。`post_comments.py` 会自动跳过该条comment并继续发布其余评论。分析时应确保行号指向diff中的新增/修改行。

### Recovery

- Token问题：提示用户检查token权限
- MR不存在：确认MR编号和项目路径
- 权限问题：建议用户检查项目成员权限
- Rate limit：显示等待时间，稍后重试
- 行号问题：检查diff hunk中的新文件行号，确保指向 `+` 行

## Best Practices

1. **增量Review**: 只评论新增或修改的代码
2. **建设性反馈**: 提供具体改进建议，不只是指出问题
3. **Context Awareness**: 考虑代码的上下文和业务逻辑
4. **Language Specific**: 遵循各语言的community standards
5. **Team Conventions**: 尊重团队已有的代码风格约定
6. **跨平台兼容**: 所有操作均通过Python脚本完成，避免使用bash特有语法

## Scripts Reference

### fetch_mr.py

获取MR的基本信息、diff和现有comments。

```bash
python3 skills/gitlab-mr-review/scripts/fetch_mr.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --mr-iid 42 \
  --token $GITLAB_TOKEN \
  --output-dir ./mr-data
```

输出文件：
- `mr_data.json`: 合并数据
- `mr_info.json`: MR基本信息
- `changes.json`: 变更统计及每文件diff
- `changes.diff`: 原始diff文本
- `existing_comments.json`: 现有comments
- `metadata.json`: 元数据

### post_comments.py

发布review comments到MR。

```bash
python3 skills/gitlab-mr-review/scripts/post_comments.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --mr-iid 42 \
  --token $GITLAB_TOKEN \
  --comments-file ./review-comments.json \
  --metadata-file ./mr-data/metadata.json
```

使用 `--dry-run` 预览comments而不实际发布。

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
