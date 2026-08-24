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

随后 Claude 会询问项目显示名（可选）和初始管理员密码（可选），其余参数走默认值。确认后自动生成。

## 默认配置

| 项目       | 默认值                                 |
| ---------- | -------------------------------------- |
| 后端框架   | FastAPI                                |
| 数据库     | PostgreSQL                             |
| Redis 缓存 | ✅                                     |
| RabbitMQ   | ⬜（ENV: `ENABLE_RABBITMQ=true` 启用） |
| Celery     | ⬜（ENV: `ENABLE_CELERY=true` 启用）   |
| MinIO      | ⬜（ENV: `ENABLE_MINIO=true` 启用）    |
| 后端端口   | 8000                                   |
| adminer UI | http://localhost:8080                  |

## 输出结构

```
my-api/
├── app/                       # FastAPI 应用（分层）
├── alembic/                   # 数据库迁移
├── docs/                      # 架构/技术栈/配置/开发/API 文档
├── tests/
├── docker/                    # Dockerfile
├── .env                       # 自动生成（含随机 SECRET_KEY）
├── .env.example
├── pyproject.toml
├── alembic.ini
├── docker-compose.yml         # postgres + redis + adminer
├── Makefile                   # start/stop/logs/install/backend-dev/db-shell/db-reset
└── 后端说明.md
```

## 启动流程

```bash
cd my-api
make start          # 启动中间件（postgres + redis + adminer）
make install        # 安装后端依赖
make backend-dev    # 启动 FastAPI 开发服务器
# 访问 http://localhost:8000/docs
# 数据库 UI： http://localhost:8080
```

## 数据库自动维护

| 状态     | 行为                                                         |
| -------- | ------------------------------------------------------------ |
| 首次启动 | 自动 `create_all` 建表 + `alembic stamp head` + 插入种子数据 |
| 后续启动 | 自动 `alembic upgrade head` + 插入缺失的种子数据             |

## 与其他命令的关系

- `/yz-init-server <name>`：本技能，纯后端 + 中间件
- `/yz-init-admin <name>`：完整前后端
- `/yz-init-ui <name>`：仅前端
