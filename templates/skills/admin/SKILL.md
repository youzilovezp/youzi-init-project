---
name: yz-init-admin
description: 一键初始化完整的管理系统（后端 + 前端 + postgresql + redis + adminer 数据库 UI + 自动维护表结构）。触发命令：「/yz-init-admin」。其他两种模式：「/yz-init-server」（后端 + 中间件）、「/yz-init-ui」（仅前端）。
---

# yz-init-admin 技能

为非技术背景或新入职工程师提供一个"开箱即用"的完整管理系统脚手架。

## 触发方式

```bash
/yz-init-admin my-app
```

随后 Claude 会通过 AskUserQuestion 询问项目显示名（可选）和初始管理员密码（可选），其余参数全部走默认值。确认后自动生成 `项目目录。

## 默认配置

| 项目       | 默认值                                           |
| ---------- | ------------------------------------------------ |
| 后端框架   | FastAPI（不可改）                                |
| 前端框架   | Vue 3 + TS + Vite（不可改）                      |
| 数据库     | PostgreSQL                                       |
| Redis 缓存 | ✅（默认启用）                                   |
| RabbitMQ   | ⬜（默认关闭，ENV: `ENABLE_RABBITMQ=true` 启用） |
| Celery     | ⬜（默认关闭，ENV: `ENABLE_CELERY=true` 启用）   |
| MinIO      | ⬜（默认关闭，ENV: `ENABLE_MINIO=true` 启用）    |
| 后端端口   | 8000                                             |
| 前端端口   | 3000                                             |
| adminer UI | http://localhost:8080（非技术用户看数据库）      |

## 输出结构

```
my-app/
├── backend/                # Python 后端（FastAPI）
├── frontend/               # 前端（Vue 3 + TS）
├── docker-compose.yml      # postgres + redis + adminer
├── Makefile                # start/stop/restart/logs/backend-dev/frontend-dev/install/db-shell/db-reset
└── 项目说明.md               # 总入口文档
```

## 执行流程

1. 询问项目显示名 + 初始管理员密码（均可选）
2. 调用 `scripts/init.py <name> --only admin`
3. 渲染 `templates/backend/*` + `templates/frontend/*` + `templates/root/*`
4. 复制到目标目录 `项目目录/`
5. 提示启动：`cd <name> && make start && make backend-dev && make frontend-dev`

## 启动后访问

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 数据库 UI：http://localhost:8080
- 默认账号：`admin` / 启动时控制台打印的随机密码

## 数据库自动维护

| 状态     | 行为                                                         |
| -------- | ------------------------------------------------------------ |
| 首次启动 | 自动 `create_all` 建表 + `alembic stamp head` + 插入种子数据 |
| 后续启动 | 自动 `alembic upgrade head` + 插入缺失的种子数据             |
| 任何失败 | 记录警告但不阻塞启动                                         |

## 与其他命令的关系

- `/yz-init-admin <name>`：本技能，前后端 + 中间件 + adminer（最常用）
- `/yz-init-server <name>`：仅后端 + 中间件
- `/yz-init-ui <name>`：仅前端
