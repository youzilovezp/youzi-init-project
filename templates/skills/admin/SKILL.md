---
name: yz-init-admin
description: 一键初始化完整的管理系统（后端 + 前端 + 中间件 + 数据库自动维护 + 本地调试）。触发命令：「/yz-init-admin」。其他两种模式：「/yz-init-server」（后端 + 中间件）、「/yz-init-ui」（仅前端）。
---

# yz-init-admin Skill

为非技术背景或新入职工程师提供一个"开箱即用"的完整管理系统脚手架。

## 触发方式

```bash
/yz-init-admin my-admin
```

随后会通过 AskUserQuestion 收集技术选型与中间件选项，确认后自动生成。

## 交互式输入

| 问题                 | 默认值      |
| -------------------- | ----------- |
| 项目名（kebab-case） | `{{input}}` |
| 后端框架             | FastAPI     |
| 数据库               | PostgreSQL  |
| 启用 Redis 缓存      | ✅          |
| 启用 RabbitMQ        | ⬜          |
| 启用 Celery 异步任务 | ⬜          |
| 启用 MinIO 对象存储  | ⬜          |
| 初始化 git           | ⬜          |

## 输出结构

```
<project-name>/
├── backend/                  # Python 后端（FastAPI）
├── frontend/                 # 前端（Vue 3 + TS + Vite）
├── docker-compose.yml        # 一键启动所有中间件
├── Makefile                  # run / start / stop / logs / clean
├── .gitignore
└── README.md                 # 总入口文档
```

## 执行流程

1. 收集用户输入（AskUserQuestion）
2. 调用 `scripts/init.py <name> --only admin [其它选项]`
3. 渲染 `templates/backend/*` 与 `templates/frontend/*` + `templates/root/*`，替换 `{{project_name}}`、`{{db_driver}}` 等变量
4. 复制到目标目录 `<project-name>/`
5. 输出启动指引：`cd <project-name> && make start`

## 模板渲染变量

- `{{ project_name }}`：项目名（kebab-case）
- `{{ project_title }}`：项目显示名
- `{{ secret_key }}`：随机生成的 64 位 hex
- `{{ db_driver }}`：asyncpg / aiomysql
- `{{ enable_redis }}`、`{{ enable_rabbitmq }}`、`{{ enable_celery }}`、`{{ enable_minio }}`：true / false

## 数据库自动维护亮点

启动时会自动维护表结构：

| 状态     | 行为                                                         |
| -------- | ------------------------------------------------------------ |
| 首次启动 | 自动 `create_all` 建表 + `alembic stamp head` + 插入种子数据 |
| 后续启动 | 自动 `alembic upgrade head` + 插入缺失的种子数据             |
| 任何失败 | 记录警告但不阻塞启动                                         |

## 与其他命令的关系

- `/yz-init-admin <name>`：本 skill，完整前后端（最常用）
- `/yz-init-server <name>`：仅后端 + 中间件（详见 yz-init-server skill）
- `/yz-init-ui <name>`：仅前端（详见 yz-init-ui skill）
