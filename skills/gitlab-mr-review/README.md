# GitLab MR Review Skill

自动化GitLab Merge Request代码审查工具，基于best practice进行多维度代码分析。

## 功能特性

- 🔍 **多维度代码分析**: 代码一致性、风格一致性、重复代码、安全性、逻辑合理性
- 🛡️ **安全检查**: SQL注入、XSS、eval/exec、敏感信息泄露等
- 📝 **Inline Comments**: 在代码行级留下具体评论
- 📊 **Review Summary**: 自动生成审查总结报告
- 🔄 **避免重复**: 智能检测已有评论，避免重复comment
- ⚙️ **可自定义**: 支持项目自定义checklist规则
- 🌐 **多语言支持**: JavaScript/TypeScript、Java、Python

## 使用方法

### 1. 配置环境变量

```bash
export GITLAB_TOKEN="your-gitlab-personal-access-token"
```

Token需要有 `api` 权限。

### 2. 使用Skill

```
帮我review一下GitLab上的这个MR：https://gitlab.com/group/project/-/merge_requests/42
```

或

```
检查这个GitLab MR的代码质量：
- GitLab URL: https://gitlab.com
- 项目: group/project
- MR编号: 42
```

### 3. 项目自定义Checklist

在项目根目录创建 `.review-checklist.md` 文件：

```markdown
# Project Review Checklist

## Custom Rules
- [ ] 所有API调用必须有超时设置
- [ ] 日志必须使用结构化格式

## Disabled Rules
- 禁用: "no_console_in_prod"
```

## 工作原理

1. **获取MR数据**: 使用GitLab API获取MR信息、diff和现有comments
2. **代码分析**: 根据检测到的编程语言，应用对应的checklist规则
3. **过滤重复**: 对比现有comments，避免重复
4. **发布评论**: 
   - Inline comments: 针对具体代码行的问题，支持GitLab Suggestions（一键应用建议）
   - Summary comment: 整体审查总结

## 支持的检查规则

### JavaScript/TypeScript

- ✅ `var` → `const`/`let`
- ✅ 避免 `eval()`
- ✅ 避免 `innerHTML`
- ✅ 使用严格相等 `===`
- ✅ 避免魔法数字
- ✅ 移除生产环境console.log

### Java

- ✅ 使用日志框架替代System.out
- ✅ SQL注入防护（PreparedStatement）
- ✅ 捕获具体异常类型
- ✅ 字符串使用equals比较

### Python

- ✅ 避免使用print
- ✅ 避免eval/exec
- ✅ 避免裸except
- ✅ 避免可变默认参数
- ✅ SQL参数化查询
- ✅ 使用 `is None` 而非 `== None`

## 目录结构

```
gitlab-mr-review/
├── SKILL.md                      # Skill定义文件
├── scripts/
│   ├── fetch_mr.py              # 获取MR数据
│   ├── analyze_code.py          # 代码分析
│   └── post_comments.py         # 发布评论
├── references/
│   ├── checklist-javascript.md  # JS/TS检查清单
│   ├── checklist-java.md        # Java检查清单
│   └── checklist-python.md      # Python检查清单
├── examples/
│   └── .review-checklist.md     # 自定义checklist示例
└── evals/
    └── evals.json               # 测试用例
```

## GitLab API

本工具使用以下GitLab API（详见官方文档）：

- **Merge Requests API**: https://docs.gitlab.com/api/merge_requests/
- **Discussions API**: https://docs.gitlab.com/api/discussions/
- **Notes API**: https://docs.gitlab.com/api/notes/

### 使用的API端点

| 操作 | 端点 | 说明 |
|------|------|------|
| 获取MR信息 | `GET /projects/:id/merge_requests/:iid` | 获取diff_refs等元数据 |
| 获取Diff | `GET /projects/:id/merge_requests/:iid/diffs` | 获取代码变更 |
| 获取Discussions | `GET /projects/:id/merge_requests/:iid/discussions` | 获取现有评论 |
| 创建Inline Comment | `POST /projects/:id/merge_requests/:iid/discussions` | 创建带position的讨论 |
| 创建General Comment | `POST /projects/:id/merge_requests/:iid/notes` | 发布总结评论 |

## 脚本说明

### fetch_mr.py

获取MR的基本信息、diff和现有comments。

```bash
python3 scripts/fetch_mr.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --mr-iid 42 \
  --token $GITLAB_TOKEN \
  --output-dir ./mr-data
```

输出文件：
- `mr_info.json`: MR基本信息
- `changes.json`: 变更统计
- `changes.diff`: Diff内容
- `existing_comments.json`: 现有comments
- `metadata.json`: 元数据（语言、分支等）

### analyze_code.py

分析代码并生成review comments。

```bash
python3 scripts/analyze_code.py \
  --changes-file ./mr-data/changes.json \
  --metadata-file ./mr-data/metadata.json \
  --existing-comments ./mr-data/existing_comments.json \
  --default-checklist-dir ./references \
  --output ./review-comments.json
```

### post_comments.py

发布comments到GitLab MR。

```bash
python3 scripts/post_comments.py \
  --gitlab-url https://gitlab.com \
  --project group/project \
  --mr-iid 42 \
  --token $GITLAB_TOKEN \
  --comments-file ./review-comments.json \
  --metadata-file ./mr-data/metadata.json
```

使用 `--dry-run` 预览comments而不实际发布：

```bash
python3 scripts/post_comments.py ... --dry-run
```

## 避免重复Comments

Skill会自动：

1. 获取MR现有的所有comments
2. 检查文件路径和行号是否匹配
3. 使用相似度算法（>80%）检测相同内容
4. 跳过已标记为resolved的问题
5. 只评论新增或修改的代码

## 扩展自定义规则

要添加自定义规则，编辑 `.review-checklist.md`：

```markdown
## Custom Rules
- [ ] 规则描述（会显示在review中）

## Disabled Rules  
- 禁用: "规则名称"

## Severity Overrides
- 将 "规则名称" 设为 critical/warning/info
```

## 注意事项

- GitLab Token需要有项目的Developer或以上权限才能发表评论
- 首次review可能需要较长时间（取决于文件数量）
- 增量review会自动跳过已评论的问题
- 二进制文件会被自动跳过

## 许可证

MIT
