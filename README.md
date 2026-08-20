# youzi-init-project

> 一键初始化完整管理系统 / 前端 / 后端工程的 Claude Code Skill。

为非技术背景或新入职工程师提供一个"开箱即用"的脚手架，支持三种粒度按需生成：

- ✅ **后端**：FastAPI + SQLAlchemy 2.0（异步）+ Pydantic v2 + JWT + Alembic
- ✅ **前端**：Vue 3 + TypeScript + Vite + Pinia + Element Plus
- ✅ **中间件**：PostgreSQL、Redis（可选）、RabbitMQ（可选）、MinIO（可选）、Celery（可选）
- ✅ **代码与配置隔离**：
  - 后端通过 pydantic-settings + `.env` 集中管理
  - 前端通过 Vite 的 `.env.[mode]` + `import.meta.env` 管理
- ✅ **自带文档**：架构、技术栈、配置、开发、API 五件套
- ✅ **数据库表结构自动维护**：首次启动自动 create_all + alembic stamp，后续启动自动 alembic upgrade
- ✅ **Docker Compose 一键启动**所有依赖

## 命令一览

| 命令              | 范围                                             | 典型用法                   |
| ----------------- | ------------------------------------------------ | -------------------------- |
| `/yz:init-admin`  | 后端 + 前端 + 中间件 + 数据库自动维护 + 本地调试 | 新建一套完整管理系统       |
| `/yz:init-ui`     | 纯前端 + 本地调试                                | 新增/替换一个前端工程      |
| `/yz:init-server` | 后端 + 中间件 + 数据库自动维护 + 本地调试        | 新增/替换一个后端 API 工程 |

## 🚀 一键安装（推荐）

```bash
cd /Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project
./install.sh install
```

`install.sh` 支持四个子命令：`install` / `uninstall` / `update` / `status`，详见 [INSTALL.md](INSTALL.md)。

## 快速体验（命令行方式）

```bash
# 1. 安装 jinja2（如果尚未安装）
pip install jinja2

# 2. 完整前后端（等价 /yz:init-admin）
python /path/to/youzi-init-project/scripts/init.py my-admin

# 仅前端（等价 /yz:init-ui）
python /path/to/youzi-init-project/scripts/init.py my-web --only ui

# 仅后端（等价 /yz:init-server，后端 + 中间件）
python /path/to/youzi-init-project/scripts/init.py my-api --only server

# 3. 进入项目
cd my-admin && make start && make backend-dev  # 终端 A
cd my-admin && make frontend-dev               # 终端 B
```

访问：

- 前端：http://localhost:5173
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 默认账号：`admin` / `admin@123456`

## 在 Claude Code 中使用

将本仓库软链接到 `~/.claude/skills/youzi-init-project/`，然后在对话中输入：

```text
/yz:init-admin my-admin
/yz:init-ui my-web
/yz:init-server my-api
```

Claude 会调用本 Skill：

1. 通过 AskUserQuestion 收集技术选型
2. 调用 `scripts/init.py --only {admin|ui|server}` 渲染模板
3. 输出项目目录

详细使用方式见 [INSTALL.md](INSTALL.md)。

## 仓库结构

```
youzi-init-project/
├── SKILL.md              # Claude Code Skill 描述（/yz:*）
├── INSTALL.md             # 安装 / 卸载 / 更新 / 使用指南
├── README.md             # 本文件
├── scripts/
│   └── init.py           # 初始化执行脚本（支持 --only）
├── templates/
│   ├── backend/          # 后端模板
│   ├── frontend/         # 前端模板
│   └── root/             # 根级中间件 + 文档
└── examples/             # 示例项目
```

## 许可证

MIT
