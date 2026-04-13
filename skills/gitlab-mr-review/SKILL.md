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

1. 获取MR的变更内容（diff）
2. 检查现有comments避免重复
3. 基于可自定义的checklist和best practice进行代码分析
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

### Step 2: Fetch MR Data

使用脚本获取MR信息和diff：

```bash
python3 scripts/fetch_mr.py \
  --gitlab-url <url> \
  --project <path> \
  --mr-iid <number> \
  --token <token> \
  --output-dir <temp-dir>
```

这会生成：
- `mr_info.json`: MR基本信息
- `changes.diff`: MR的diff内容
- `existing_comments.json`: 现有的review comments

### Step 3: Analyze Code

根据检测到的编程语言，读取对应的checklist：

1. 检查项目根目录是否有 `.review-checklist.md`
2. 如果没有，使用内置的 `references/checklist-{language}.md`
3. 分析代码，标记问题

分析维度：
- **代码一致性**: 命名规范、代码结构、API使用一致性
- **风格一致性**: 代码格式、缩进、空格、括号
- **重复代码**: 可提取的公共逻辑、DRY原则
- **代码安全性**: 注入风险、敏感信息暴露、不安全的函数使用
- **逻辑合理性**: 边界条件处理、错误处理、空值检查

### Step 4: Check for Duplicates

将新发现的问题与 `existing_comments.json` 中的现有comments对比：

- 检查相同文件和行号
- 检查相同或相似的问题描述
- 如果问题已被标记且没有后续变更，跳过
- 如果问题已被标记但有新变更，更新comment

### Step 5: Post Review Comments

使用脚本发布comments：

```bash
python3 scripts/post_comments.py \
  --gitlab-url <url> \
  --project <path> \
  --mr-iid <number> \
  --token <token> \
  --comments-file <comments.json>
```

对于每个问题，创建inline discussion：
- 指定文件路径和行号
- 提供清晰的问题描述
- 建议改进方案（如果适用）

### Step 6: Post Summary Comment

在MR上发布总结评论，包含：
- 审查概览（发现问题数量、按严重程度分类）
- 主要问题类别统计
- 建议的后续行动
- 可选的Approve/Request Changes状态

## Scripts Reference

### fetch_mr.py

获取MR信息和现有comments。

**Input**:
```json
{
  "gitlab_url": "https://gitlab.com",
  "project_path": "group/project",
  "mr_iid": 42,
  "token": "glpat-xxx"
}
```

**Output**:
- `mr_info.json`: MR详情
- `changes.diff`: Diff内容
- `existing_comments.json`: 现有comments列表

### post_comments.py

发布review comments到MR。

**Input**:
```json
{
  "gitlab_url": "https://gitlab.com",
  "project_path": "group/project",
  "mr_iid": 42,
  "token": "glpat-xxx",
  "comments": [
    {
      "file_path": "src/main.js",
      "line": 15,
      "type": "issue",
      "severity": "warning",
      "message": "使用var声明变量，建议使用const或let",
      "suggestion": "将 `var x = ...` 改为 `const x = ...`"
    }
  ]
}
```

## Review Checklist Templates

### 内置Checklist格式

每个语言的checklist位于 `references/checklist-{language}.md`：

```markdown
# {Language} Review Checklist

## Code Consistency
- [ ] 命名规范遵循项目约定
- [ ] 函数/方法长度合理（不超过50行）
- [ ] 避免魔法数字，使用常量

## Style Consistency
- [ ] 代码格式化工具配置一致
- [ ] 缩进和空格使用统一

## Code Duplication
- [ ] 无重复代码块（超过5行）
- [ ] 公共逻辑已提取为函数/类

## Security
- [ ] 无SQL注入风险
- [ ] 无XSS漏洞
- [ ] 敏感信息未硬编码

## Logic
- [ ] 边界条件已处理
- [ ] 错误处理完整
- [ ] 空值/undefined检查
```

### 项目自定义Checklist

项目可以创建 `.review-checklist.md` 覆盖或扩展内置规则：

```markdown
# Project Review Checklist

## Custom Rules
- [ ] 所有API调用必须有超时设置
- [ ] 日志必须使用结构化格式
- [ ] 数据库查询必须使用参数化

## Disabled Rules
- 禁用: "函数长度检查"（本项目允许长函数）
```

## Comment Format

### Inline Comment Structure

```markdown
**{severity}**: {issue_type}

{description}

**建议**:
{suggestion}

**参考**: {reference_link}
```

### Severity Levels

- **critical**: 阻塞性问题（安全漏洞、明显bug）
- **warning**: 需要关注（风格问题、潜在问题）
- **info**: 建议性意见（可以忽略）

## Avoiding Duplicate Comments

在发布新comment前，检查现有comments：

1. **相同位置**: 检查相同文件+行号是否有相同类型的comment
2. **相同内容**: 使用fuzzy match检查描述相似度 > 80%
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
4. 运行 `fetch_mr.py` 获取MR数据
5. 检测编程语言（从changed files推断）
6. 读取checklist（先检查 `.review-checklist.md`，再使用内置）
7. 分析代码，生成review comments
8. 过滤掉与现有comments重复的问题
9. 发布inline comments
10. 发布summary comment

### 输出示例

**Summary Comment**:

```markdown
## 📝 MR Review Summary

**Reviewed**: src/utils.js, src/api.js, tests/utils.test.js

### 发现的问题

| Severity | Count |
|----------|-------|
| 🔴 Critical | 1 |
| 🟡 Warning | 3 |
| 🔵 Info | 2 |

### 主要问题

1. **Security** (Critical): `api.js:23` - 用户输入未转义直接拼接到SQL查询
2. **Style** (Warning): `utils.js:45` - 函数超过50行，建议拆分
3. **Duplication** (Warning): 两处相同的错误处理逻辑，建议提取

### 建议行动

- [ ] 修复SQL注入风险
- [ ] 重构过长函数
- [ ] 考虑提取公共错误处理逻辑

---
*This review was generated automatically. Please feel free to discuss any suggestions.*
```

## Error Handling

### Common Errors

- **401 Unauthorized**: Token无效或权限不足
- **404 Not Found**: MR不存在或已删除
- **403 Forbidden**: 没有review权限
- **API Rate Limit**: 遇到rate limit时等待并重试

### Recovery

- Token问题：提示用户检查token权限
- MR不存在：确认MR编号和项目路径
- 权限问题：建议用户检查项目成员权限
- Rate limit：显示等待时间，稍后重试

## Best Practices

1. **增量Review**: 只评论新增或修改的代码
2. **建设性反馈**: 提供具体改进建议，不只是指出问题
3. **Context Awareness**: 考虑代码的上下文和业务逻辑
4. **Language Specific**: 遵循各语言的community standards
5. **Team Conventions**: 尊重团队已有的代码风格约定

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
    - `new_line`: 行号

### Notes API

- **Create MR note**: `POST /projects/:id/merge_requests/:merge_request_iid/notes`
  - 文档: https://docs.gitlab.com/api/notes/#create-a-merge-request-note
  - 发布general comments（非inline的summary评论）

### GitLab Suggestions

Inline comments支持GitLab的Suggestion功能，格式为：

```markdown
```suggestion
建议的代码内容
```
```

这允许开发者一键应用建议的修改。

### Authentication

所有API请求使用 `Private-Token` HTTP Header进行认证：

```
Private-Token: <your_access_token>
```

需要的Token权限：
- `api` - 访问GitLab API
- 项目访问权限（Developer或更高角色）
