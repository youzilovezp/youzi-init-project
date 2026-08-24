---
name: yz-init-server
description: 一键初始化后端 API 工程（FastAPI + postgresql + redis + adminer 数据库 UI + 自动维护表结构）。触发命令：「/yz-init-server」。其他两种模式：「/yz-init-admin」（完整前后端）、「/yz-init-ui」（仅前端）。
---

# yz-init-server 技能

为非技术背景或新入职工程师提供一个"开箱即用"的后端 API 工程脚手架。

## 触发方式

```bash
/yz-init-server my-api
```

Claude 会询问项目显示名（可选）和初始管理员密码（可选），其余走默认值。

## 默认配置

| 配置              | 默认值                      |
| ----------------- | --------------------------- |
| 后端框架          | FastAPI                     |
| 数据库            | PostgreSQL                  |
| Redis             | ✅                          |
| adminer 数据库 UI | ✅（http://localhost:8080） |
| 后端端口          | 8000                        |

## 执行流程

1. 询问项目显示名 + 初始管理员密码（均可回车跳过）
2. 调用 `scripts/init.py <name> --only server`
3. 渲染 `templates/backend/*` + `templates/root/*`，文件放在项目根目录
4. 复制到目标目录
5. 提示启动：`cd <name> && make install && make start && make backend-dev`

## 启动后访问

- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 数据库 UI：http://localhost:8080
- 默认账号：`admin` / 启动时控制台打印的随机密码

## 常用 Make 命令

- `make start` / `make stop` — 中间件启停
- `make backend-dev` — 本地启动
- `make db-shell` — 进入 psql
- `make reset-admin` / `make admin-pass NEW=xxx` — 重置密码
- `make backup` / `make restore FILE=...` — 备份恢复
- `make db-reset` — ⚠️ 清空所有数据

## 与其他命令的关系

- `/yz-init-admin <name>`：完整前后端
- `/yz-init-ui <name>`：纯前端
