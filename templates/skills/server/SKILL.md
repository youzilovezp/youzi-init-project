---
name: yz-init-server
description: 一键初始化后端 API 工程（FastAPI + PostgreSQL + adminer 数据库 UI + 自动维护表结构；中间件优先复用本机已运行的）。触发命令：「/yz-init-server」。
allowed-tools: Bash(python*scripts/init.py*), Bash(python*add_module*), Read, Write, Edit, Glob, Grep
---

# yz-init-server 技能

为非技术背景或新入职工程师提供一个"开箱即用"的后端 API 工程脚手架。

## 触发方式

```bash
/yz-init-server my-api
```

AI（Claude Code / opencode）会询问项目显示名（可选）和初始管理员密码（可选），其余全部走默认值。

## 默认配置

| 配置     | 默认值                     |
| -------- | -------------------------- |
| 后端框架 | FastAPI                    |
| 数据库   | **PostgreSQL**（复用本机/起 Docker） |
| Redis    | ❌（默认不用；限流走内存） |
| 后端端口 | 8000                       |

> **中间件策略**：默认 PostgreSQL——`make start` 优先**复用本机已运行的**，缺的才用 Docker 起。
> 限流默认走进程内内存；生产多 worker 加 `--with-redis` 启用 Redis。
> 想要零依赖单文件体验：`.env` 改 `DB_TYPE=sqlite`。

## 执行流程

1. 询问项目显示名 + 初始管理员密码（均可回车跳过）
2. 调用 `scripts/init.py <name> --only server`
3. 渲染 `templates/backend/*` + `templates/root/*`，文件放在项目根目录
4. 复制到目标目录
5. 提示启动：`cd <name> && make dev`（一键：装依赖 + 中间件 + 后端）

## 启动后访问

- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 数据库 UI（adminer）：http://localhost:8080（`make start` 后可选启动）
- 默认账号：`admin` / `admin`（本地开发方便；**生产前必须用 `--admin-pass` 改强密码**）

## 常用 Make 命令

- `make dev` — 一键启动（装依赖 + 中间件 + 后端）
- `make install` — 首次装依赖（创建 venv）
- `make backend-dev` — 本地启动
- `make test` — 跑测试
- `make reset-admin` / `make admin-pass NEW=xxx` — 重置密码
- `make backup` — 备份数据库到 backups/
- `make use-sqlite` / `make use-pg` — 一键切换数据库模式
- `make db-migrate MSG="描述"` / `make db-upgrade` / `make db-downgrade` — 数据库迁移
- `make start` / `make stop` — 中间件启停（**优先复用本机已运行的服务**，缺的用 Docker 起；backend-dev 会自动调用）

## 与其他命令的关系

- `/yz-init-admin <name>`：完整前后端
- `/yz-init-ui <name>`：纯前端
