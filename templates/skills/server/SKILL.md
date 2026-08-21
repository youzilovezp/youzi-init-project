---
name: yz-init-server
description: 一键初始化后端 API 工程（纯后端 + 中间件 + 数据库自动维护 + 本地调试）。触发命令：「/yz-init-server」。其他两种模式：「/yz-init-admin」（完整前后端）、「/yz-init-ui」（仅前端）。
---

# yz-init-server Skill

为非技术背景或新入职工程师提供一个"开箱即用"的后端 API 工程脚手架。

## 触发方式

```bash
/yz-init-server my-api
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
├── app/                       # FastAPI 应用（分层）
├── alembic/                   # 数据库迁移
├── docs/                      # 架构/技术栈/配置/开发/API 文档
├── tests/
├── docker/
├── .env                       # 自动生成（含随机 SECRET_KEY）
├── .env.example
├── pyproject.toml
├── alembic.ini
├── docker-compose.yml         # 一键启动中间件
├── Makefile                   # start / stop / logs / backend-dev / install
└── README.md
```

## 执行流程

1. 收集用户输入（AskUserQuestion）
2. 调用 `scripts/init.py <name> --only server [其它选项]`
3. 渲染 `templates/backend/*` + `templates/root/*`，替换变量
4. 复制到目标目录
5. 输出启动指引：`cd <project-name> && make start && make backend-dev`

## 数据库自动维护

| 状态     | 行为                                                         |
| -------- | ------------------------------------------------------------ |
| 首次启动 | 自动 `create_all` 建表 + `alembic stamp head` + 插入种子数据 |
| 后续启动 | 自动 `alembic upgrade head` + 插入缺失的种子数据             |

## 典型启动流程

```bash
cd my-api
make start          # 启动中间件
make install        # 安装后端依赖
make backend-dev    # 启动 FastAPI 开发服务器
# 访问 http://localhost:59001/docs
```

## 与其他命令的关系

- `/yz-init-server <name>`：本 skill，纯后端 + 中间件
- `/yz-init-admin <name>`：完整前后端（详见 yz-init-admin skill）
- `/yz-init-ui <name>`：仅前端（详见 yz-init-ui skill）
