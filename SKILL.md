---
name: yz-init
description: 一键初始化完整的管理系统 / 前端 / 后端工程（Python FastAPI + Vue 3）。中间件体系完善、代码与配置隔离，自带架构/技术栈/配置/开发文档。触发短语：「/yz:init-admin」「/yz:init-ui」「/yz:init-server」「初始化脚手架」「创建管理系统」「创建前端工程」「创建后端工程」。
---

# YZ Init Scaffold Skill

为非技术背景或新入职工程师提供一个"开箱即用"的脚手架，支持**三种粒度**按需生成：

| 命令                     | 范围                    | 典型场景                   |
| ------------------------ | ----------------------- | -------------------------- |
| `/yz:init-admin <name>`  | **完整前后端** + 中间件 | 新建一套完整管理系统       |
| `/yz:init-ui <name>`     | **仅前端**              | 新增/替换一个前端工程      |
| `/yz:init-server <name>` | **后端 + 中间件**       | 新增/替换一个后端 API 工程 |

## 一、触发方式

```bash
/yz:init-admin    my-admin      # 完整前后端
/yz:init-ui       my-web        # 仅前端
/yz:init-server   my-api        # 仅后端
```

随后会通过 AskUserQuestion 收集技术选型与中间件选项，确认后自动生成。

## 二、交互式输入（admin / server）

| 问题                 | 默认值      |
| -------------------- | ----------- |
| 项目名（kebab-case） | `{{input}}` |
| 后端框架             | FastAPI     |
| 数据库               | PostgreSQL  |
| 启用 Redis 缓存      | ✅          |
| 启用 RabbitMQ        | ⬜          |
| 启用 Celery 异步任务 | ⬜          |
| 启用 MinIO 对象存储  | ⬜          |

## 三、交互式输入（ui）

| 问题                 | 默认值       |
| -------------------- | ------------ |
| 项目名（kebab-case） | `{{input}}`  |
| UI 组件库            | Element Plus |
| 启用国际化 i18n      | ✅           |

## 四、输出结构

### `/yz:init-admin` 输出

```
<project-name>/
├── backend/                  # Python 后端（FastAPI）
├── frontend/                 # 前端（Vue 3 + TS + Vite）
├── docker-compose.yml        # 一键启动所有中间件
├── Makefile                  # run / start / stop / logs / clean
├── .gitignore
└── README.md                 # 总入口文档
```

### `/yz:init-ui` 输出

```
<project-name>/
├── src/
├── public/
├── docs/
├── .env.development
├── .env.production
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

### `/yz:init-server` 输出

```
<project-name>/
├── app/
├── alembic/
├── docs/
├── tests/
├── docker/
├── .env                  # 自动生成（含随机 SECRET_KEY）
├── .env.example
├── pyproject.toml
├── alembic.ini
├── docker-compose.yml    # 一键启动中间件
├── Makefile              # start / stop / logs / backend-dev / install
└── README.md
```

## 五、执行流程

1. 收集用户输入（AskUserQuestion）
2. 调用 `scripts/init.py <name> --only {admin|ui|server} [其它选项]`
3. 渲染 `templates/` 中对应子目录的模板，替换 `{{project_name}}`、`{{db_driver}}` 等变量
4. 复制到目标目录
5. 输出启动指引

## 六、模板渲染约定

模板中变量使用 `{{var_name}}` 占位，常量包括：

- `{{ project_name }}`：项目名（kebab-case）
- `{{ project_title }}`：项目显示名
- `{{ secret_key }}`：随机生成的 64 位 hex
- `{{ db_driver }}`：asyncpg / aiomysql
- `{{ enable_redis }}`、`{{ enable_rabbitmq }}`、`{{ enable_celery }}`、`{{ enable_minio }}`、`{{ enable_i18n }}`：true / false

详见 `scripts/init.py` 中的 `build_context()` 实现。

## 七、与之前 `/init-scaffold` 的关系

旧命令 `/init-scaffold` 等价于 `/yz:init-admin`，保留兼容。后续统一使用 `/yz:*` 前缀。
