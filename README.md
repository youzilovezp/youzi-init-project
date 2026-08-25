<div align="center">

<img src="assets/youzi-logo.svg?v=3" width="110" alt="youzi logo"/>

# 🍊 柚子脚手架 · 一站式项目初始化工具

**`/yz-init-admin <name>` → 完整前后端 + 中间件 + 数据库自动维护 → 开箱即跑**

![License](https://img.shields.io/badge/License-MIT-orange.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet.svg)

[📖 使用手册](使用手册.md) · [📦 安装说明](安装说明.md) · [⚙️ SKILL](templates/skills/admin/SKILL.md)

</div>

---

## ⚡ 它是什么

给非技术背景或新入职工程师的 **Claude Code 脚手架 skill**。**一条命令**生成完整可跑的管理系统,自带数据库表结构自动维护、admin 随机密码、API 文档、adminer 数据库 UI。

```
/yz-init-admin my-app
       │
       ▼
🛠️ 渲染 → 模板引擎(Jinja2)+ 真实随机密码注入 .env
       │
       ▼
📦 输出 → backend/(FastAPI) + frontend/(Vue 3) + docker-compose + 文档
       │
       ▼
🚀 启动 → make install → make start → make backend-dev / make frontend-dev
```

> 💡 Claude Code 不支持 `:` 作为命令字符,所以三个独立 skill 用 `-` 分隔:`yz-init-admin` / `yz-init-server` / `yz-init-ui`

---

## ✨ 核心能力

|     | 能力                     | 说明                                                            |
| --- | ------------------------ | --------------------------------------------------------------- |
| 🛠️  | **3 种粒度**             | `admin`(完整前后端)/ `server`(纯后端)/ `ui`(纯前端)             |
| ⚡  | **FastAPI + 异步**       | SQLAlchemy 2.0 async + Pydantic v2 + JWT                        |
| 🎨  | **Vue 3 + Element Plus** | TypeScript + Vite + Pinia + 自动按需导入                        |
| 🐳  | **中间件一键启动**       | PostgreSQL 16 + Redis 7 + adminer(看数据用)                     |
| 🔐  | **安全默认**             | bcrypt 密码 + JWT 黑名单 + CORS + TrustedHost + 慢速限流        |
| 🗄️  | **数据库自动维护**       | 首次 `create_all` → 后续 `alembic upgrade head` 全自动          |
| 🌱  | **种子数据**             | admin + 3 个 demo 用户(密码启动时控制台打印)                    |
| 📦  | **一键加业务模块**       | `add_module.py` 生成 model/schema/crud/router/view/api 6 个文件 |
| 📚  | **自带完整文档**         | 每个生成项目含架构/技术栈/配置/开发/API 5 份文档                |

---

## 🚀 三步开始

### ① 安装

```bash
git clone <repo> && cd youzi-init-project
./install.sh install
```

按提示确认后,会创建三个 skill 到 `~/.claude/skills/`。

### ② 在 Claude Code 中使用

```bash
/yz-init-admin my-app      # 完整前后端 + 中间件
/yz-init-server my-api     # 后端 + 中间件
/yz-init-ui my-web         # 仅前端
```

Claude 会询问项目显示名和初始管理员密码(都可回车跳过),确认后自动生成 `my-app/`。

### ③ 启动新项目

```bash
cd my-app
make install       # 首次:安装后端 + 前端依赖
make start         # 启动 PostgreSQL + Redis + adminer
make backend-dev   # 终端 A:启动后端(uvicorn --reload)
make frontend-dev  # 终端 B:启动前端(vite dev)
```

启动后可访问:

| 服务         | 地址                       | 说明             |
| ------------ | -------------------------- | ---------------- |
| 🖥️ 前端      | http://localhost:3000      | Vue 3 SPA        |
| 🔌 后端 API  | http://localhost:8000      | FastAPI          |
| 📖 API 文档  | http://localhost:8000/docs | Swagger UI       |
| 🗄️ 数据库 UI | http://localhost:8080      | adminer          |
| 🔑 默认账号  | `admin` / **随机密码**     | 启动时控制台打印 |

---

## 📋 三个模式对比

| 模式         | 适合                 | 输出                        | 启动命令                                 |
| ------------ | -------------------- | --------------------------- | ---------------------------------------- |
| **`admin`**  | 🆕 新建一套完整系统  | 后端 + 前端 + 中间件 + 文档 | `make backend-dev` + `make frontend-dev` |
| **`server`** | 🔧 新增/替换后端 API | 后端 + 中间件 + 文档        | `make backend-dev`                       |
| **`ui`**     | 🎨 新增/替换前端     | 纯前端 + 文档               | `pnpm dev`                               |

---

## 🔧 技术栈

### 后端

|     | 技术           | 版本       |
| --- | -------------- | ---------- |
| 🐍  | Python         | 3.11+      |
| ⚡  | FastAPI        | 0.110+     |
| 🗄️  | SQLAlchemy     | 2.0 async  |
| 📦  | Pydantic       | v2         |
| 🔐  | PyJWT + bcrypt | 内置       |
| 🔄  | Alembic        | 1.13+      |
| 📝  | loguru         | 结构化日志 |

### 前端

|     | 技术         | 版本 |
| --- | ------------ | ---- |
| 🖼️  | Vue          | 3.4  |
| 📘  | TypeScript   | 5.4  |
| ⚡  | Vite         | 5.1  |
| 🎨  | Element Plus | 2.6  |
| 📦  | Pinia        | 2.1  |
| 🧪  | Vitest       | 1.5  |

### 中间件

|     | 服务       | 镜像                 |
| --- | ---------- | -------------------- |
| 🐘  | PostgreSQL | postgres:16.4-alpine |
| 🔴  | Redis      | redis:7.2-alpine     |
| 🗄️  | adminer    | adminer:4.8.1        |

---

## 📁 仓库结构

```
youzi-init-project/
├── 📦 安装说明.md           # 安装指南(系统要求 + 三种安装方式 + 卸载)
├── 📖 使用手册.md           # 使用手册(上手 + 三模式 + 加业务模块 + FAQ + 排错)
├── 👋 README.md             # 你正在看(项目总览)
├── 🔧 install.sh            # 一键安装脚本(install/uninstall/update/status)
├── 📂 scripts/              # 模板渲染工具
│   ├── init.py              ⭐ admin/server/ui 三模式渲染
│   └── add_module.py        ⭐ 给生成项目加业务模块(6 个文件)
├── 🎨 templates/            # 所有模板
│   ├── backend/             后端(FastAPI + SQLAlchemy + JWT + Alembic)
│   ├── frontend/            前端(Vue 3 + TS + Vite + Element Plus)
│   ├── root/                根级(docker-compose + Makefile + .gitignore + 文档)
│   └── skills/              三个 SKILL.md(给 Claude 看的触发入口)
└── 🖼️ assets/youzi-logo.svg # 项目 logo
```

---

## 🧩 加业务模块

```bash
cd my-app
python backend/scripts/add_module.py order --title "订单管理" \
    --fields "name:str,price:float:0,stock:int:0,status:str:active"
```

自动生成 **6 个文件** + 提示 **5 处手动注册**:

| 文件                                    | 位置            |
| --------------------------------------- | --------------- |
| 📄 `app/models/order.py`                | ORM 模型        |
| 📄 `app/schemas/order.py`               | Pydantic schema |
| 📄 `app/crud/order.py`                  | CRUD 类         |
| 📄 `app/api/v1/endpoints/order.py`      | FastAPI router  |
| 📄 `frontend/src/api/order.ts`          | 前端 TS 接口    |
| 📄 `frontend/src/views/order/index.vue` | 前端 CRUD 页面  |

支持字段类型:`str` / `text` / `int` / `float` / `bool` / `datetime`

---

## 📚 文档导航

| 📄 文档                                                                 | 👤 适合谁                              | ⏱️ 时间 |
| ----------------------------------------------------------------------- | -------------------------------------- | ------- |
| [📖 使用手册.md](使用手册.md)                                           | 🟢 任何人 · 4 大块(上手/进阶/FAQ/排错) | 15 分钟 |
| [📦 安装说明.md](安装说明.md)                                           | 🟢 第一次安装 · 装/卸/更新             | 5 分钟  |
| [⚙️ templates/skills/admin/SKILL.md](templates/skills/admin/SKILL.md)   | 🔴 Claude 触发入口(不是给人读)         | 5 分钟  |
| [⚙️ templates/skills/server/SKILL.md](templates/skills/server/SKILL.md) | 🔴 server 模式 Skill                   | 5 分钟  |
| [⚙️ templates/skills/ui/SKILL.md](templates/skills/ui/SKILL.md)         | 🔴 ui 模式 Skill                       | 5 分钟  |

**怎么选**:

- 🆕 还没装 → [📦 安装说明.md](安装说明.md)
- 🚀 装好想用 → [📖 使用手册.md § 1-3](使用手册.md)
- 🧩 想加业务模块 → [📖 使用手册.md § 4](使用手册.md)
- ❓ 踩坑 → [📖 使用手册.md § 6 排错](使用手册.md)

---

## 🛠️ 先决条件

| 工具            | 用途                    | 安装                                                 |
| --------------- | ----------------------- | ---------------------------------------------------- |
| 🐍 Python 3.11+ | 运行 `init.py`          | 系统包管理器                                         |
| 📦 jinja2       | 模板渲染(`init.py` 用)  | `pip install jinja2`(项目根自带 `install.sh` 会提示) |
| 🐳 Docker       | 启动 PostgreSQL + Redis | [docker.com](https://docker.com)                     |
| 🤖 Claude Code  | 调用 skill              | [claude.ai/code](https://claude.ai/code)             |

---

## 📄 License

MIT

---

<div align="center">

**Made with 🔥 by Claude Code** —— 让 1 个命令 = 1 个完整可跑的管理系统 🍊

</div>
