# 个人技能工具集

一些自用的自动化小工具，基于 Claude Code 的 Skill 机制实现。

## 包含工具

### dockerhub-to-aliyun-acr-sync

将 Docker Hub 镜像同步到阿里云 ACR 个人版。适合需要穿越 GFW 获取镜像的场景。

**功能**
- 支持指定平台（linux/amd64, linux/arm64 等）
- 两阶段工作流：先拉取（Docker Hub 网络）→ 后推送（阿里云网络）
- 自动推导仓库名，保持 tag 一致

**前置条件**
- Docker CLI
- 阿里云 ACR 个人版仓库
- 环境变量：
  ```bash
  export ALIYUN_ACR_REGISTRY=crpi-xxx.cn-shanghai.personal.cr.aliyuncs.com/your-namespace
  export ALIYUN_ACR_USERNAME=your-username
  export ALIYUN_ACR_PASSWORD=your-password
  ```

**使用示例**
```bash
# 进入 skill 目录
cd skills/dockerhub-to-aliyun-acr-sync

# 同步单个镜像
docker pull --platform linux/amd64 ubuntu/apache2:2.4-21.10_beta
docker tag ubuntu/apache2:2.4-21.10_beta $ALIYUN_ACR_REGISTRY/apache2:2.4-21.10_beta
docker push $ALIYUN_ACR_REGISTRY/apache2:2.4-21.10_beta
```

详见 [SKILL.md](skills/dockerhub-to-aliyun-acr-sync/SKILL.md)

---

### grant-gitlab

在 GitLab 上给指定用户添加项目访问权限。省去在网页上点来点去的麻烦。

**功能**
- 通过用户名和项目名快速授权
- 支持 Guest/Reporter/Developer/Maintainer 四种角色
- 自动处理用户已存在时的权限更新

**前置条件**
- GitLab API Token
- 环境变量：
  ```bash
  export GITLAB_TOKEN=your-private-token
  ```

**使用示例**
```bash
# 默认 Developer 角色
curl -X POST -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  -d '{"user_id": 123, "access_level": 30}' \
  "https://gitlab.example.com/api/v4/projects/456/members"

# 角色对应值：10=Guest, 20=Reporter, 30=Developer, 40=Maintainer
```

详见 [SKILL.md](skills/grant-gitlab/SKILL.md)

---

## 安装方法

这些 Skill 设计用于 Claude Code 环境，也可单独使用。

### 方式一：Claude Code Skill 安装（推荐）

```bash
# 在 Claude Code 中安装
claude config set skills.dockerhub-to-aliyun-acr-sync.path /path/to/skills/dockerhub-to-aliyun-acr-sync
claude config set skills.grant-gitlab.path /path/to/skills/grant-gitlab
```

安装后可直接对话使用：
- "帮我把 nginx:1.27.3 同步到阿里云"
- "给张三添加 myproject 的 Developer 权限"

### 方式二：独立使用

每个 Skill 目录下的 SKILL.md 都包含完整的手动执行步骤，复制其中的 shell 命令即可独立运行。

---

## 项目结构

```
skills/
├── dockerhub-to-aliyun-acr-sync/    # Docker 镜像同步
│   └── SKILL.md                     # 完整使用说明
└── grant-gitlab/                    # GitLab 权限管理
    └── SKILL.md                     # 完整使用说明
```

---

## 许可证

MIT - 随意使用，后果自负。
