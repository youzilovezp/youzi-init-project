---
name: yz-init-ui
description: 一键初始化前端工程（Vue 3 + TS + Vite + Element Plus，支持本地调试）。触发命令：「/yz-init-ui」。其他两种模式：「/yz-init-admin」（完整前后端）、「/yz-init-server」（后端 + 中间件）。
---

# yz-init-ui 技能

为非技术背景或新入职工程师提供一个"开箱即用"的前端工程脚手架。

## 触发方式

```bash
/yz-init-ui my-web
```

Claude 会询问项目显示名（可选），其余走默认值。

## 默认配置

| 配置     | 默认值                           |
| -------- | -------------------------------- |
| 前端框架 | Vue 3 + TS + Vite + Element Plus |
| 前端端口 | 3000                             |
| 后端代理 | http://localhost:8000            |

## 执行流程

1. 询问项目显示名（可选）
2. 调用 `scripts/init.py <name> --only ui`
3. 渲染 `templates/frontend/*`
4. 复制到目标目录
5. 提示启动：`cd <name> && pnpm install && pnpm dev`

## 启动流程

```bash
cd my-web
pnpm install
pnpm dev
# 访问 http://localhost:3000
```

## 与其他命令的关系

- `/yz-init-admin <name>`：完整前后端
- `/yz-init-server <name>`：后端 + 中间件
