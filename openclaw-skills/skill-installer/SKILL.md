---
name: skill-installer
description: >
  从 ClawHub 下载并安装 OpenClaw skills。
  自动处理下载、解压、安装到正确目录的完整流程。
  触发词：安装 skill、下载 skill、skill install
author: hugogu
version: 1.0.0
---

# Skill Installer

从 ClawHub 自动下载并安装 OpenClaw skills。

## 安装流程

### Step 1: 解析 Skill 信息

从用户输入提取：
- 作者 (owner)
- Skill 名称 (slug)
- 完整格式：`author/skill-name` 或 `https://clawhub.ai/author/skill-name`

### Step 2: 获取下载 URL

1. 访问 ClawHub 页面获取元数据
2. 提取真实的下载链接（通常是 `https://*.convex.site/api/v1/download?slug=xxx`）
3. **注意**：直接访问 skill 页面返回的是 HTML，不是 zip 文件

### Step 3: 下载 Zip 文件

```bash
curl -L -o /tmp/{skill-name}.zip "{download-url}"
```

验证下载的是 zip 文件：`file /tmp/{skill-name}.zip` 应返回 "Zip archive data"

### Step 4: 解压

**重要**：系统可能没有 `unzip` 命令，使用 Python 解压：

```bash
python3 -c "import zipfile; zipfile.ZipFile('/tmp/{skill-name}.zip').extractall('/tmp/{skill-name}')"
```

### Step 5: 安装到 Skills 目录

```bash
cp -r /tmp/{skill-name} ~/.openclaw/skills/{skill-name}
```

### Step 6: 验证

检查文件是否存在：
- `~/.openclaw/skills/{skill-name}/SKILL.md`
- `~/.openclaw/skills/{skill-name}/_meta.json` (如果有)

## 常见错误及解决

| 错误 | 原因 | 解决 |
|------|------|------|
| "Not a zip file" | 下载的是 HTML 页面 | 需要找到真实的 download URL |
| "unzip: not found" | 系统没有 unzip | 使用 Python 解压 |
| "Invalid skill slug" | CLI 格式不支持 | 使用手动安装方式 |
| 批准超时 | 用户没及时批准 | 提醒用户保持在线 |

## 使用示例

**用户**: "安装 antonia-sz/opinion-analyzer"

**执行**:
1. 解析出 owner=antonia-sz, slug=opinion-analyzer
2. 访问 https://clawhub.ai/antonia-sz/opinion-analyzer 获取 download URL
3. 下载 zip 到 /tmp/opinion-analyzer.zip
4. 用 Python 解压到 /tmp/opinion-analyzer/
5. 复制到 ~/.openclaw/skills/opinion-analyzer/
6. 验证安装成功

## 注意事项

- 下载 URL 可能是临时生成的，不要缓存
- 始终使用 Python 解压（兼容性最好）
- 安装前检查是否已存在同名 skill（询问是否覆盖）
- 安装后更新 TOOLS.md 的 Local Skills Inventory
