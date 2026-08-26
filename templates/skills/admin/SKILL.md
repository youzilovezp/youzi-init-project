---
name: yz-init-admin
description: 一键初始化完整的管理系统（后端 + 前端 + PostgreSQL + adminer 数据库 UI + 自动维护表结构；中间件优先复用本机已运行的）。触发命令：「/yz-init-admin」。
allowed-tools: Bash(python*scripts/init.py*), Bash(python*add_module*), Read, Write, Edit, Glob, Grep
---

# yz-init-admin 技能

为非技术背景或新入职工程师提供一个"开箱即用"的完整管理系统脚手架。

## 触发方式

```bash
/yz-init-admin my-app
```

AI（Claude Code / opencode）会询问项目显示名（可选）和初始管理员密码（可选），其余全部走默认值。确认后自动生成 `项目目录`。

## 默认配置（用户不需要选）

| 配置     | 默认值                      |
| -------- | --------------------------- |
| 后端框架 | FastAPI                     |
| 前端框架 | Vue 3 + TS + Vite           |
| 数据库   | **PostgreSQL**（复用本机/起 Docker） |
| Redis    | ❌（默认不用；限流走内存）  |
| 后端端口 | 8000                        |
| 前端端口 | 3000                        |

> **中间件策略**：默认 PostgreSQL——`make start` 优先**复用本机已运行的**，缺的才用 Docker 起。
> 限流默认走进程内内存；生产多 worker 加 `--with-redis` 启用 Redis。
> 想要零依赖单文件体验：`.env` 改 `DB_TYPE=sqlite`。

## 执行流程

1. 询问项目显示名 + 初始管理员密码（均可回车跳过）
2. 调用 `scripts/init.py <name> --only admin`（生产级加 `--with-redis`）
3. 渲染 `templates/backend/*` + `templates/frontend/*` + `templates/root/*`
4. 复制到目标目录 `项目目录/`
5. 提示启动：`cd <name> && make dev`（一键：装依赖 + 中间件 + 前后端；或分开 `make backend-dev` / `make frontend-dev`）

## 启动后用户访问

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 数据库 UI（adminer）：http://localhost:8080（`make start` 后可选启动）
- 默认账号：`admin` / `admin`（本地开发方便；**生产前必须用 `--admin-pass` 改强密码**）

## 日常用到的 Make 命令（生成项目里有 `make help`）

- `make dev` — 一键启动：装依赖 + 中间件 + 前后端（Ctrl+C 一起停）
- `make install` — 首次装依赖（后端 venv + 前端 node_modules）
- `make backend-dev` / `make frontend-dev` — 本地开发
- `make test` — 跑测试
- `make reset-admin` / `make admin-pass NEW=xxx` — 忘了密码？重置
- `make backup` — 备份数据库到 backups/
- `make use-sqlite` / `make use-pg` — 一键切换数据库模式
- `make db-migrate MSG="描述"` — 生成迁移文件
- `make db-upgrade` — 应用所有迁移
- `make db-downgrade` — 回滚一步
- `make start` / `make stop` — 中间件启停（**优先复用本机已运行的服务**，缺的用 Docker 起；backend-dev 会自动调用）

## 加新业务模块

```bash
python3 backend/scripts/add_module.py order --title "订单管理"
```

自动生成 model/schema/crud/router/view/api 六个文件。脚本会提示**5 处手动操作**：

1. `backend/app/models/__init__.py` 加 `from app.models.<name> import <Cls>`
2. `backend/app/api/v1/router.py` 加 `from ... import router as <name>_router` + `api_router.include_router(...)`
3. `frontend/src/router/index.ts` 加路由记录
4. `frontend/src/layouts/BasicLayout.vue` 加菜单项
5. 生成数据库迁移：`make db-migrate MSG="add <name>" && make db-upgrade`

带自定义字段（避免后续手动改 5 个文件）：

```bash
python3 backend/scripts/add_module.py product --title "商品管理" \
    --fields "name:str,price:float:0,stock:int:0,status:str:active"
```

支持类型：`str / text / int / float / bool / datetime`。详细文档看生成项目根目录的 `项目说明.md`。

## 与其他命令的关系

- `/yz-init-server <name>`：纯后端
- `/yz-init-ui <name>`：纯前端
