# youzi-init-project

> 一键初始化完整管理系统 / 前端 / 后端工程的 Claude Code Skill 仓库。

为非技术背景或新入职工程师提供一个"开箱即用"的脚手架，支持三种粒度按需生成：

- ✅ **后端**：FastAPI + SQLAlchemy 2.0（异步）+ Pydantic v2 + JWT + Alembic
- ✅ **前端**：Vue 3 + TypeScript + Vite + Pinia + Element Plus
- ✅ **中间件**：PostgreSQL、Redis（可选）、RabbitMQ（可选）、MinIO（可选）、Celery（可选）
- ✅ **代码与配置隔离**
- ✅ **自带文档**：架构、技术栈、配置、开发、API 五件套
- ✅ **数据库表结构自动维护**：首次启动自动 create_all + alembic stamp，后续启动自动 alembic upgrade
- ✅ **Docker Compose 一键启动**所有依赖

## 命令一览（安装后 Claude Code 中可见）

| 命令                     | 范围                                             | 典型场景                   |
| ------------------------ | ------------------------------------------------ | -------------------------- |
| `/yz-init-admin <name>`  | 后端 + 前端 + 中间件 + 数据库自动维护 + 本地调试 | 新建一套完整管理系统       |
| `/yz-init-server <name>` | 后端 + 中间件 + 数据库自动维护 + 本地调试        | 新增/替换一个后端 API 工程 |
| `/yz-init-ui <name>`     | 纯前端 + 本地调试                                | 新增/替换一个前端工程      |

> **说明**：Claude Code 不支持 `:` 作为 slash command 字符，所以三个独立 skill 用 `-` 分隔。

## 🚀 一键安装（推荐）

```bash
cd /Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project
./install.sh install
```

`install.sh` 默认会创建三个独立 skill：

```
~/.claude/skills/yz-init-admin/    → /yz-init-admin
~/.claude/skills/yz-init-server/   → /yz-init-server
~/.claude/skills/yz-init-ui/       → /yz-init-ui
```

共享 scripts 和 templates（符号链接），修改源仓库即时生效。

`install.sh` 支持四个子命令：`install` / `uninstall` / `update` / `status`，详见 [INSTALL.md](INSTALL.md)。

## 快速体验（命令行方式）

```bash
# 1. 安装 jinja2（如果尚未安装）
pip install jinja2

# 2. 完整前后端
python /path/to/youzi-init-project/scripts/init.py my-admin

# 仅前端
python /path/to/youzi-init-project/scripts/init.py my-web --only ui

# 仅后端（后端 + 中间件）
python /path/to/youzi-init-project/scripts/init.py my-api --only server

# 3. 进入项目
cd my-admin && make start && make backend-dev  # 终端 A
cd my-admin && make frontend-dev               # 终端 B
```

访问：

- 前端：http://localhost:199310
- 后端：http://localhost:199311
- API 文档：http://localhost:199311/docs
- 默认账号：`admin` / `youzi@123456`

## 在 Claude Code 中使用

```text
/yz-init-admin my-admin
/yz-init-server my-api
/yz-init-ui my-web
```

详细使用方式见 [INSTALL.md](INSTALL.md)。
