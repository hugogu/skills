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

### docker-deploy

创建完整的 Docker 虚拟化部署基础设施，包括 docker-compose 编排、多环境支持、镜像仓库管理和网络感知的构建脚本。

**功能**
- 单命令启动完整应用栈（应用服务 + 依赖服务）
- 支持本地开发（从 Dockerfile 构建）和生产环境（使用预构建镜像）
- Registry 前缀切换，轻松切换不同环境（本地/测试/生产）
- 精细化版本控制，所有第三方镜像使用固定版本（无 latest）
- 网络感知脚本，所有推送操作在最后执行，减少网络切换

**前置条件**
- Docker CLI
- docker-compose
- 镜像仓库访问权限（用于生产部署）

**使用示例**
```bash
# 设置项目 Docker 部署
# Claude 会自动创建以下结构：
# deploy/
# ├── docker-compose.yml          # 主编排文件
# ├── .env.template              # 环境变量模板
# ├── scripts/
# │   └── build-and-push.sh      # 构建推送脚本
# └── services/
#     └── api/
#         └── Dockerfile

# 本地开发
cd deploy
docker-compose up --build

# 构建并推送到生产仓库
./scripts/build-and-push.sh --registry registry.example.com --version 1.0.0

# 生产环境部署
docker-compose pull
docker-compose up -d
```

详见 [SKILL.md](skills/docker-deploy/SKILL.md)

---

---

### metabase-query

通过 Metabase MCP 安全地创建 Query、Dashboard 并执行 SQL 查询，内置数据库性能保护机制。

**功能**
- 自动检查表结构和索引，避免生成低效的全表扫描 SQL
- 调研阶段强制限制输出行数（LIMIT 100），防止拖垮数据库
- 提供 SQL 安全检查脚本，识别潜在性能问题
- 生成符合安全规范的 SQL 查询模板
- 支持创建原生 SQL Question 和可视化 Dashboard

**前置条件**
- Metabase 实例已部署
- 已配置 Metabase MCP Server
- 数据库连接已配置

**使用示例**
```bash
# 在 Claude Code 中使用
# 用户说："帮我创建一个查询最近7天订单的 Metabase Question"

# Claude 会：
# 1. 检查表结构和索引
# 2. 生成安全的 SQL（带 LIMIT）
# 3. 通过 Metabase MCP 创建 Question

# SQL 安全检查（独立使用）
cd skills/metabase-query
python scripts/check_sql.py "SELECT * FROM orders WHERE created_at > '2024-01-01'"

# 生成 SQL 模板
python scripts/generate_template.py time_series table=orders time_column=created_at value_column=amount days=7
```

详见 [SKILL.md](skills/metabase-query/SKILL.md)

---

### git-commit

智能 Git 提交工具，提交前自动同步远程、判断是否 amend，并生成 Conventional Commits 格式的提交信息。

**功能**
- 提交前 `git fetch` 检查远程是否有新提交，有则先 `git pull --rebase` 同步
- 遇到 rebase 冲突立即终止，输出冲突文件列表和逐步解决命令
- 严格判断是否 amend 上一次提交（type + scope 完全相同且未推送才 amend）
- 自动生成符合 [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) 规范的提交信息
- footer 中附加当前 Agent 及 Model 信息

**触发方式**
- "帮我提交代码"
- "commit this"
- "/commit"
- "save my changes"

详见 [SKILL.md](skills/git-commit/SKILL.md)

---

## 安装方法

这些 Skill 设计用于 Claude Code 环境，也可单独使用。

### 方式一：Claude Code Skill 安装（推荐）

```bash
# 安装指定 skill
npx skills add https://github.com/hugogu/skills --skill metabase-query
npx skills add https://github.com/hugogu/skills --skill dockerhub-to-aliyun-acr-sync
npx skills add https://github.com/hugogu/skills --skill grant-gitlab
npx skills add https://github.com/hugogu/skills --skill docker-deploy
npx skills add https://github.com/hugogu/skills --skill git-commit
```

安装后可直接对话使用：
- "帮我把 nginx:1.27.3 同步到阿里云"
- "给张三添加 myproject 的 Developer 权限"
- "为我的 Node.js 项目设置 Docker 部署"
- "帮我创建一个查询最近7天订单的 Metabase Dashboard"

### 方式二：独立使用

每个 Skill 目录下的 SKILL.md 都包含完整的手动执行步骤，复制其中的 shell 命令即可独立运行。

---

## 项目结构

```
skills/
├── git-commit/                      # 智能 Git 提交
│   └── SKILL.md                     # 完整使用说明
├── dockerhub-to-aliyun-acr-sync/    # Docker 镜像同步
│   └── SKILL.md                     # 完整使用说明
├── grant-gitlab/                    # GitLab 权限管理
│   └── SKILL.md                     # 完整使用说明
├── docker-deploy/                   # Docker 部署基础设施
│   ├── SKILL.md                     # 完整使用说明
│   ├── scripts/                     # 构建推送脚本
│   ├── references/                  # 模板参考
│   └── examples/                    # 使用示例
├── metabase-query/                  # Metabase 查询与 Dashboard
│   ├── SKILL.md                     # 完整使用说明
│   └── scripts/                     # SQL 安全检查脚本
└── prisma-migrations/               # Prisma 迁移管理
    ├── SKILL.md                     # 完整使用说明
    ├── scripts/                     # 迁移脚本
    └── reference/                   # 参考配置
```

---

## 许可证

MIT - 随意使用，后果自负。
