<div align="center">

<img src="assets/youzi-logo.svg?v=3" width="110" alt="youzi logo"/>

# 🍊 youzi-init-project · 一站式项目初始化工具

**给非技术背景的宝宝：`一条命令` → 完整可跑的管理系统**

![License](https://img.shields.io/badge/License-MIT-orange.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet.svg)

[📖 使用手册](使用手册.md) · [📦 安装说明](安装说明.md) · [⚙️ SKILL 源码](templates/skills/admin/SKILL.md)

</div>

---

## 🚀 30 秒上手

```bash
# 1. 在 Claude Code 里输入（项目目录可随便换）
/yz-init-admin my-app

# 2. 按提示回答（可全回车跳过）→ my-app/ 生成

# 3. 一键启动（默认 PostgreSQL——自动复用本机已有的，缺的用 Docker 起）
cd my-app && make dev
```

打开 **http://localhost:3000**，账号 `admin` / `admin`，登录成功 ✅

> 💡 默认密码 `admin/admin` 方便本地开发。**生产前用 `python scripts/init.py my-app --admin-pass '<强密码>'` 重设。**

---

## 🤔 这是什么？

**一个 Claude Code 的脚手架 skill**：你说一个名字，Claude 自动把完整的管理系统代码、配置、文档一次性生成到本地。

```
你输入：/yz-init-admin my-app
        │
        ▼
Claude 做：
  📋 询问显示名 + 初始密码（都可跳过）
  🛠️  用 Jinja2 渲染所有模板（FastAPI + Vue 3 + PostgreSQL + SQLAlchemy…）
  🔐  生成 64 位随机 SECRET_KEY 写入 .env
  🌱  首次启动自动建表 + 种子账号
  📦  生成 backend/ + frontend/ + Makefile + 文档
        │
        ▼
你拿到：
  my-app/
  ├── backend/            # FastAPI 后端（data/app.db 是 SQLite 数据库）
  │   ├── app/            # models / api / crud / core
  │   └── alembic/        # 数据库迁移
  ├── frontend/           # Vue 3 SPA
  ├── docker-compose.yml  # PostgreSQL/Redis（仅生产模式用）
  └── Makefile            # make backend-dev / frontend-dev / db-migrate
```

---

## 🎯 三种模式，按需选

| 模式 | 适合场景 | 输出 | 启动命令 |
|---|---|---|---|
| **`admin`** | 🆕 新建一套完整系统 | 后端 + 前端 + 文档 | `make backend-dev` + `make frontend-dev` |
| **`server`** | 🔧 接已有前端，加后端 | 后端 + 文档 | `make backend-dev` |
| **`ui`** | 🎨 接已有后端，加前端 | 纯前端 + 文档 | `pnpm dev` |

> 📌 三种模式都用 `-` 分隔（不用 `:` 是因为 Claude Code 不支持冒号作命令字符）。

---

## ✨ 生成的项目长这样

### 🔧 后端（FastAPI + SQLAlchemy 2.0 异步）

| 模块 | 路径 | 作用 |
|---|---|---|
| API 路由 | `app/api/v1/endpoints/` | 认证、用户、角色 CRUD |
| 依赖注入 | `app/api/deps.py` | SessionDep / CurrentUser / SuperUser |
| 配置 | `app/core/config.py` | pydantic-settings 从 .env 加载 |
| 安全 | `app/core/security.py` | JWT（带 jti）+ bcrypt |
| 异常 | `app/core/exceptions.py` | 统一响应码 + 全局处理 |
| 数据库 | `app/db/init_db.py` | 启动自动建表 + 种子数据 |
| 迁移 | `alembic/` | 后续 `make db-migrate MSG=...` 增量更新 |

### 🎨 前端（Vue 3 + TypeScript + Vite）

| 模块 | 路径 | 作用 |
|---|---|---|
| 路由守卫 | `src/router/index.ts` | 未登录跳 `/login`，无权限跳首页 |
| 请求拦截 | `src/api/request.ts` | 401 弹窗 + token 自动注入 + 错误统一处理 |
| 用户状态 | `src/stores/user.ts` | token 持久化 + login/logout |
| 布局 | `src/layouts/BasicLayout.vue` | 侧边栏 + 顶栏 + el-menu |
| 页面 | `src/views/system/{user,role}/` | 用户/角色 CRUD |

### 🗄️ 数据库

| 场景 | 方案 |
|---|---|
| 默认 | **PostgreSQL**——`make start` **优先复用本机已运行的**，缺的才用 Docker 起（adminer 数据库 UI 可选） |
| 零依赖体验 | `.env` 改 `DB_TYPE=sqlite`（单文件 `backend/data/app.db`） |

---

## 🧩 加业务模块（可选）

```bash
cd my-app
python backend/scripts/add_module.py order --title "订单管理" \
  --fields "name:str,price:float:0,stock:int:0,status:str:active"
```

自动生成 **6 个文件**（后端 model/schema/crud/router + 前端 API/页面），需要手动注册 **5 处**：

1. `backend/app/models/__init__.py` 加 import
2. `backend/app/api/v1/router.py` 加路由
3. `frontend/src/router/index.ts` 加路由记录
4. `frontend/src/layouts/BasicLayout.vue` 加菜单项
5. `make db-migrate MSG="add order" && make db-upgrade`

详细：[使用手册 § 5](使用手册.md#5-加业务模块-add_modulepy)

---

## 📚 文档导航

| 你想了解什么 | 看这里 |
|---|---|
| 🆕 第一次装脚手架 | [📦 安装说明.md](安装说明.md) |
| 🚀 装好后怎么用 / 怎么加模块 | [📖 使用手册.md](使用手册.md) |
| 🛠️ 模板里某个文件改坏了 | [templates/backend/](templates/backend/) 源码 |
| 🤖 给 Claude 看怎么触发 | [templates/skills/admin/SKILL.md](templates/skills/admin/SKILL.md) |
| ❌ 出错了 | [使用手册 § 6 排错](使用手册.md#6-faq--故障排查) |

---

## 🔧 技术栈一览

### 后端
| | 技术 | 版本 |
|---|---|---|
| 🐍 | Python | 3.11+ |
| ⚡ | FastAPI | 0.110+ |
| 🗄️ | SQLAlchemy | 2.0 async |
| 💾 | PostgreSQL（默认，16）/ SQLite（可选） | — |
| 📦 | Pydantic | v2 |
| 🔐 | PyJWT + bcrypt | 内置 |
| 🔄 | Alembic | 1.13+ |

### 前端
| | 技术 | 版本 |
|---|---|---|
| 🖼️ | Vue | 3.4 |
| 📘 | TypeScript | 5.4 |
| ⚡ | Vite | 5.1 |
| 🎨 | Element Plus | 2.6 |
| 📦 | Pinia | 2.1 |

---

## 🤝 贡献 / 自定义模板

模板就是仓库里 `templates/` 下的所有内容——符号链接安装下改了**即时生效**。

```bash
cd youzi-init-project
# 直接改 templates/backend/app/main.py.tmpl
vim templates/backend/app/main.py.tmpl
# 下次 /yz-init-admin 生成项目时自动应用
```

更多：[使用手册 § 4.3](使用手册.md#43-改模板)

---

## 📄 License

MIT
