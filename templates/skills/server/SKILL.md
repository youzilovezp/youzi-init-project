---
name: yz-init-server
description: 一键初始化后端 API 工程（FastAPI + SQLite 数据库，零配置免装 Docker，自动维护表结构）。触发命令：「/yz-init-server」。
allowed-tools: Bash(python*scripts/init.py*), Read, Write, Edit, Glob, Grep
---

# yz-init-server 技能

为非技术背景或新入职工程师提供一个"开箱即用"的后端 API 工程脚手架。

## 触发方式

```bash
/yz-init-server my-api
```

Claude 会询问项目显示名（可选）和初始管理员密码（可选），其余全部走默认值。

## 默认配置

| 配置     | 默认值                     |
| -------- | -------------------------- |
| 后端框架 | FastAPI                    |
| 数据库   | **SQLite**（文件，零配置） |
| Redis    | ❌（默认不用；限流走内存） |
| 后端端口 | 8000                       |

> **零配置启动**：默认 SQLite + 进程内内存限流，**不需要 Docker**。
> 要用生产级 PostgreSQL/Redis：跑 `init.py` 时加 `--with-redis`，再把 `.env` 改 `DB_TYPE=postgresql`。

## 执行流程

1. 询问项目显示名 + 初始管理员密码（均可回车跳过）
2. 调用 `scripts/init.py <name> --only server`
3. 渲染 `templates/backend/*` + `templates/root/*`，文件放在项目根目录
4. 复制到目标目录
5. 提示启动：`cd <name> && make install && make backend-dev`

## 启动后访问

- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 默认账号：`admin` / `admin`（本地开发方便；**生产前必须用 `--admin-pass` 改强密码**）

## 常用 Make 命令

- `make install` — 首次装依赖（创建 venv）
- `make backend-dev` — 本地启动
- `make test` — 跑测试
- `make reset-admin` / `make admin-pass NEW=xxx` — 重置密码
- `make db-migrate MSG="描述"` / `make db-upgrade` / `make db-downgrade` — 数据库迁移
- `make start` / `make stop` — 中间件启停（仅 PG/Redis 模式需要；**优先复用本机已运行的服务**）

## 与其他命令的关系

- `/yz-init-admin <name>`：完整前后端
- `/yz-init-ui <name>`：纯前端
