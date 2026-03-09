---
name: grant-gitlab
description: 在 GitLab 上给指定用户添加指定项目的访问权限。当用户提到给用户授权、添加成员、授予项目访问权限、add user to project、grant access、project permission 等相关操作时使用此 skill。
---

# GitLab 项目成员授权

当用户请求给某个 GitLab 项目添加用户访问权限时，使用此 skill。

## 使用方式

用户可以使用以下格式：
- `/grant-gitlab 用户名 项目名` - 默认使用 Developer 角色
- `/grant-gitlab 用户名 项目名 角色名` - 指定角色

支持的访问级别：
- `guest` - 访客（只读）
- `reporter` - 报告者（只读 + 下载）
- `developer` - 开发者（推送代码，默认）
- `maintainer` - 维护者（管理设置）

## 执行步骤

### 1. 解析参数

从用户输入中提取：
- **用户名**: 要授权的用户名（如 `hugogu`）
- **项目名**: 项目名称或 namespace/project 格式（如 `app` 或 `backend/api`）
- **访问级别**: 如未指定默认为 `developer`

### 2. 获取 GitLab 配置

- **GitLab URL**: `https://gitlab.baofoo.net/`
- **Token**: 从环境变量 `GITLAB_TOKEN` 获取

**Windows 环境变量获取方式**：
```powershell
# 使用 PowerShell 获取（推荐）
[Environment]::GetEnvironmentVariable('GITLAB_TOKEN', 'Machine')
[Environment]::GetEnvironmentVariable('GITLAB_TOKEN', 'User')
```

### 3. 查找项目

优先使用搜索 API 获取项目 ID（更可靠）：

```
GET /api/v4/projects?search={project_name}&membership=true
```

返回结果中查找 `path_with_namespace` 匹配的项目。

如果已知完整路径（namespace/project），可直接使用（需 URL 编码 `/`）：
```
GET /api/v4/projects/{namespace}%2F{project}
```

项目名可能是：
- 纯项目名（如 `app`）- 使用搜索 API
- namespace/project 格式（如 `mygroup/app`）- 使用搜索 API 或 URL 编码直接获取

### 4. 查找用户

通过用户名查找用户 ID：

```
GET /api/v4/users?username={username}
```

### 5. 添加项目成员

调用 API 添加成员（使用 curl 发送请求）：

```bash
curl -s -X POST -H "PRIVATE-TOKEN: {token}" -H "Content-Type: application/json" \
  -d '{"user_id": {user_id}, "access_level": {access_level}}' \
  "https://gitlab.baofoo.net/api/v4/projects/{project_id}/members"
```

**注意**：WebFetch 工具不支持自定义请求头，必须使用 curl。

访问级别值：
- `10` - Guest
- `20` - Reporter  
- `30` - Developer
- `40` - Maintainer

### 6. 返回结果

成功时返回：
```
✅ 已成功将 {username} 添加为 {project_name} 的 {role} 角色
用户 ID: {user_id}
项目 ID: {project_id}
```

如果用户已是成员，更新其权限。

## 错误处理

- 如果找不到项目：提示用户检查项目名称是否正确；确认项目是否存在于用户可访问范围内（使用 `membership=true` 搜索）
- 如果找不到用户：提示用户检查用户名是否正确，尝试使用 `search` 参数模糊搜索
- 如果 Token 无效（401）：提示检查 GITLAB_TOKEN 环境变量；在 Windows 上使用 PowerShell 获取
- 如果权限不足（403）：提示需要 Maintainer 或 Owner 权限
- 如果用户已是成员：GitLab 会自动更新其权限级别

## 实际调用示例

```bash
# 1. 获取 Token（Windows PowerShell）
$token = [Environment]::GetEnvironmentVariable('GITLAB_TOKEN', 'Machine')

# 2. 搜索项目
curl -s -H "PRIVATE-TOKEN: $token" "https://gitlab.baofoo.net/api/v4/projects?search=myproject&membership=true"

# 3. 查找用户
curl -s -H "PRIVATE-TOKEN: $token" "https://gitlab.baofoo.net/api/v4/users?username=username"

# 4. 添加成员（access_level: 10=guest, 20=reporter, 30=developer, 40=maintainer）
curl -s -X POST -H "PRIVATE-TOKEN: $token" -H "Content-Type: application/json" \
  -d '{"user_id": 123, "access_level": 30}' \
  "https://gitlab.baofoo.net/api/v4/projects/456/members"
```
