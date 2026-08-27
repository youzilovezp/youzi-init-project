---
name: yz-init-ui
description: 一键初始化前端工程（Vue 3 + TS + Vite + Naive UI，支持本地调试）。触发命令：「/yz-init-ui」。
allowed-tools: Bash(python*scripts/init.py*), Read, Write, Edit, Glob, Grep
---

# yz-init-ui 技能

为非技术背景或新入职工程师提供一个"开箱即用"的前端工程脚手架。

## 触发方式

```bash
/yz-init-ui my-web
```

AI（Claude Code / opencode）会询问项目显示名（可选），其余走默认值。

## 默认配置

| 配置     | 默认值                           |
| -------- | -------------------------------- |
| 前端框架 | Vue 3 + TS + Vite + Naive UI |
| 前端端口 | 3000                             |
| 后端代理 | http://localhost:8000            |

## 执行流程

1. 询问项目显示名（可选）
2. 调用 `scripts/init.py <name> --only ui`（`--only` 必填，绝不可省略）
3. 渲染 `templates/frontend/*`
4. 复制到目标目录
5. 提示启动：`cd <name> && pnpm install && pnpm dev`

## 启动流程

```bash
cd my-web
pnpm install
pnpm dev
# 访问 http://localhost:3000
# UI 预览模式：内置 mock API（无后端），admin/admin 登录
```

## 与其他命令的关系

- `/yz-init-admin <name>`：完整前后端
- `/yz-init-server <name>`：后端 + 中间件
