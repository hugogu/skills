---
name: wiki-deploy
description: |
  部署/重新部署 Wiki.js 服务到远程服务器 ali-sh。连接 SSH 执行 docker compose pull && up -d。
  当用户说"重新部署 Wiki"、"更新 Wiki 服务"、"重启 Wiki"、"发 Wiki"、"部署 wiki" 时使用。
triggers:
  - "重新部署 wiki"
  - "部署 wiki"
  - "更新 wiki 服务"
  - "重启 wiki"
  - "发 wiki"
  - "wiki deploy"
  - "redeploy wiki"
metadata:
  runtime: none
  prerequisites:
    - SSH config 中已配置 ali-sh（位于 ~/.ssh/config）
    - ali-sh 上 /mnt/wiki-compose/ 目录存在且包含 docker-compose.yml
    - Docker 和 docker compose 已在 ali-sh 上安装
---

# Wiki Deploy

将 Wiki.js 服务部署/重新部署到远程服务器 ali-sh。

## 部署步骤

```bash
ssh ali-sh 'cd /mnt/wiki-compose && docker compose pull && docker compose up -d'
```

该命令依次执行：
1. **SSH 连接到 ali-sh**（主机 8.153.166.17，用户 root，密钥 ~/.ssh/id_rsa）
2. **进入 Wiki 目录** `/mnt/wiki-compose`
3. **拉取最新镜像** `docker compose pull`
4. **重新创建并启动容器** `docker compose up -d`

## 执行方式

直接在 exec 中运行 SSH 命令，等待完成即可：

```javascript
const { execSync } = require('child_process');
const output = execSync("ssh ali-sh 'cd /mnt/wiki-compose && docker compose pull && docker compose up -d'", { timeout: 120000 });
```

## 预期输出

成功时输出类似：
```
db Pulled
wiki Pulled
Container wiki-db  Running
Container wiki-portal  Recreated
Container wiki-portal  Started
```

## 错误处理

| 错误 | 原因 | 处理 |
|------|------|------|
| SSH 连接超时 | ali-sh 网络不可达 | 检查服务器状态，重试 |
| `docker compose pull` 失败 | 镜像仓库不可达 | 检查网络，检查 docker 登录状态 |
| `docker compose up -d` 失败 | Compose 配置问题 | 检查 /mnt/wiki-compose/docker-compose.yml |
| `Container wiki-portal  Running` 未出现 | 容器启动失败 | 用 `ssh ali-sh 'docker logs wiki-portal --tail 50'` 查看日志 |

## 验证

部署完成后验证服务可用：
1. 访问 https://wiki.hugogu.cn 确认页面正常加载
2. 如果页面异常，查看容器日志排查

## 相关 Skill

- **wiki-writer** — 编写 Wiki.js 兼容的 Markdown 内容
- **wiki-publisher** — 通过 GraphQL API 发布内容到 Wiki.js
