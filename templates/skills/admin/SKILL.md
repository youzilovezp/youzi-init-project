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

Claude 会询问项目显示名（可选）和初始管理员密码（可选），其余全部走默认值。确认后自动生成 `项目目录`。

## 默认配置（用户不需要选）

| 配置              | 默认值                      |
| ----------------- | --------------------------- |
| 后端框架          | FastAPI                     |
| 前端框架          | Vue 3 + TS + Vite           |
| 数据库            | PostgreSQL                  |
| Redis             | ✅（已启用）                |
| adminer 数据库 UI | ✅（http://localhost:8080） |
| 后端端口          | 8000                        |
| 前端端口          | 3000                        |

## 执行流程

1. 询问项目显示名 + 初始管理员密码（均可回车跳过）
2. 调用 `scripts/init.py <name> --only admin`
3. 渲染 `templates/backend/*` + `templates/frontend/*` + `templates/root/*`
4. 复制到目标目录 `项目目录/`
5. 提示启动：`cd <name> && make install && make start && make backend-dev && make frontend-dev`

## 启动后用户访问

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 数据库 UI：http://localhost:8080
- 默认账号：`admin` / 启动时控制台打印的随机密码

## 日常用到的 Make 命令（生成项目里有 `make help`）

- `make start` / `make stop` — 中间件启停
- `make backend-dev` / `make frontend-dev` — 本地开发
- `make db-shell` — 进入 psql 命令行
- `make reset-admin` — 忘了密码？重置
- `make backup` / `make restore FILE=...` — 备份恢复
- `make db-reset` — ⚠️ 清空所有数据

## 加新业务模块

```bash
python backend/scripts/add_module.py order --title "订单管理"
```

自动生成 model/schema/crud/router/view/api 六个文件，提示用户 4 处手动注册。

## 与其他命令的关系

- `/yz-init-server <name>`：纯后端 + 中间件
- `/yz-init-ui <name>`：纯前端
