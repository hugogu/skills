---
name: publish-to-wiki
description: |
  **TRIGGER WORDS:** "发到wiki"、"发wiki"、"publish to wiki"、"wiki发布"、"同步到wiki"
  
  **USE WHEN:**
  - 用户说"把 xxx.md 发到wiki"
  - 用户说"同步到wiki"
  - 用户要求发布/上传/推送 markdown 内容到 Wiki.js
  - 处理 workspace 中的 .md 文件并发布到 wiki.hugogu.cn
  
  **DO NOT USE:** 当用户只是查询/读取 wiki 内容时（用 feishu_fetch_doc）

  此 skill 用于将本地 markdown 文件发布到 Wiki.js，处理格式转换、API 认证、路径规划。
metadata: {"env": [{"name": "WIKI_KEY", "description": "Wiki.js API token (generate in Admin > API Access)", "required": true, "credential": true}, {"name": "WIKI_URL", "description": "Wiki.js GraphQL endpoint, e.g. https://your-wiki.example.com/graphql", "required": true}], "primaryCredential": "WIKI_KEY", "runtime": {"python": {"deps": ["requests"]}}}
---

# Publish to Wiki

将本地 Markdown 文件发布到 Wiki.js 知识库。

## 触发场景（按优先级排序）

### 1. 文件路径 + 发 Wiki（最高优先级）
当用户消息包含：
- "把 `/path/to/file.md` 发到 wiki"
- "同步 `xxx.md` 到 wiki"
- "发布 `article.md` 到 wiki"
- "`wiki_xxx.md` 发到我的 wiki"

**立即触发此 skill**。

### 2. 直接发布指令
- "发到 wiki"
- "发 wiki"
- "publish to wiki"
- "wiki 发布"
- "上传 wiki"
- "推送 wiki"

### 3. 创建 Wiki 页面
- "创建 wiki 页面"
- "新建 wiki 文章"
- "在 wiki 上发篇文章"

## 快速使用流程

```
用户：把 /root/.openclaw/workspace/article.md 发到 wiki
      ↓
AI：读取 SKILL.md → 读取 article.md → 确定路径 → 发布 → 返回链接
```

## 前置检查

发布前必须确认：
1. **读取 SKILL.md** - 确保按正确流程执行
2. **读取目标文件** - 获取完整 markdown 内容
3. **确定发布路径** - 根据内容类型建议路径（见下表）
4. **确认标题** - 从文件 H1 标题或文件名提取

## 路径规划

| 内容类型 | 建议路径 | 示例 |
|---------|---------|------|
| 技术文档/架构设计 | `tech/{领域}/{主题}` | `tech/backend/rpc-guide` |
| 产品设计/PRD | `product/{系统}/{文档}` | `product/risk-engine/prd` |
| 风控/支付相关 | `fintech/{主题}` | `fintech/risk/design-patterns` |
| 新闻/日报 | `news/{年}/{月}/{日期}` | `news/2026/04/2026-04-08` |
| 个人笔记 | `notes/{分类}/{主题}` | `notes/ideas/architecture` |
| 项目文档 | `projects/{项目}/{文档}` | `projects/openclaw/skill-dev` |

## 发布步骤

### Step 1: 读取文件
```python
with open("/path/to/file.md", "r", encoding="utf-8") as f:
    content = f.read()
```

### Step 2: 提取元信息
- **标题**: 从文件第一行 `# Title` 提取，或文件名转换
- **路径**: 根据内容类型建议，与用户确认
- **描述**: 取前 100-200 字摘要
- **标签**: 根据内容关键词提取 3-6 个

### Step 3: 发布到 Wiki
```python
import json
import requests
import os

WIKI_URL = "https://wiki.hugogu.cn/graphql"
WIKI_KEY = os.environ["WIKI_KEY"]

query = '''
mutation CreatePage($content: String!, $title: String!, $path: String!, 
                   $description: String!, $tags: [String]!) {
  pages {
    create(
      content: $content
      title: $title
      path: $path
      description: $description
      tags: $tags
      editor: "markdown"
      isPublished: true
      isPrivate: false
      locale: "zh"
    ) {
      page {
        id
        path
        title
      }
    }
  }
}
'''

variables = {
    "content": content,  # 原始 markdown，无需预处理
    "title": title,
    "path": path,  # 格式: "category/sub-category/page-name"
    "description": description,
    "tags": tags
}

payload = json.dumps({"query": query, "variables": variables})

response = requests.post(
    WIKI_URL,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WIKI_KEY}"
    },
    data=payload
)

result = response.json()
```

### Step 4: 返回结果
```
✅ 发布成功！
- 标题：{title}
- 链接：https://wiki.hugogu.cn/{path}
- 页面ID：{id}
```

## 格式处理规则

### 自动清理
- ✅ **保留**: 所有 markdown 格式、代码块、表格、链接
- ✅ **保留**: HTML 标签（Wiki.js 支持）
- ❌ **移除**: YAML frontmatter（`---` 包裹的元数据）

### 路径规范
- 使用小写字母
- 用连字符 `-` 代替空格
- 路径层级建议 2-4 级
- 避免特殊字符（保留 `/` 作为分隔符）

## 常见错误处理

| 错误 | 原因 | 解决方案 |
|-----|------|---------|
| `Unauthorized` | API Key 无效 | 检查 `WIKI_KEY` 环境变量 |
| `Page already exists` | 路径冲突 | 询问用户是更新还是换路径 |
| `ValidationError` | 字符串转义问题 | 使用 GraphQL Variables，不要手动转义 |
| 超时 | 内容太大 | 分批发布或优化内容 |

## 完整示例

### 场景：发布技术文章

**用户指令**: "把 wiki_rpc_article.md 发到 wiki"

**执行流程**:
```python
# 1. 读取文件
with open("/root/.openclaw/workspace/wiki_rpc_article.md", "r") as f:
    content = f.read()

# 2. 提取标题（第一行 H1）
title = "RPC协议深度解析：从原理到实践"  # 从 # RPC协议深度解析... 提取

# 3. 确定路径
path = "tech/backend/rpc-protocol-guide"

# 4. 提取描述（前200字）
description = "深入解析RPC远程过程调用协议，涵盖核心架构、主流框架对比..."

# 5. 设置标签
tags = ["RPC", "分布式系统", "微服务", "技术架构", "gRPC", "Dubbo"]

# 6. 发布
# ... GraphQL mutation ...

# 7. 返回结果
print("✅ 发布成功！")
print("链接: https://wiki.hugogu.cn/tech/backend/rpc-protocol-guide")
```

## 参考

- Wiki.js GraphQL API: https://docs.requarks.io/dev/api
- GraphQL 变量最佳实践: https://graphql.org/learn/queries/#variables
