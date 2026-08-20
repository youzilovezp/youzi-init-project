---
name: yz-init-ui
description: 一键初始化前端工程（Vue 3 + TS + Vite + Element Plus，支持本地调试）。触发命令：「/yz-init-ui」。其他两种模式：「/yz-init-admin」（完整前后端）、「/yz-init-server」（后端 + 中间件）。
---

# yz-init-ui Skill

为非技术背景或新入职工程师提供一个"开箱即用"的前端工程脚手架。

## 触发方式

```bash
/yz-init-ui my-web
```

随后会通过 AskUserQuestion 收集前端技术选型，确认后自动生成。

## 交互式输入

| 问题                 | 默认值       |
| -------------------- | ------------ |
| 项目名（kebab-case） | `{{input}}`  |
| UI 组件库            | Element Plus |
| 启用国际化 i18n      | ✅           |
| 初始化 git           | ⬜           |

## 输出结构

```
<project-name>/
├── src/
│   ├── api/                   # 接口层（Axios 拦截器）
│   ├── components/
│   ├── config/
│   ├── layouts/               # BasicLayout 等
│   ├── router/                # 路由 + 全局守卫
│   ├── stores/                # Pinia
│   ├── views/                 # 页面
│   ├── styles/
│   ├── types/
│   ├── utils/
│   ├── App.vue
│   └── main.ts
├── public/
├── docs/                      # 架构/技术栈/配置/开发文档
├── .env.development
├── .env.production
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

## 执行流程

1. 收集用户输入（AskUserQuestion）
2. 调用 `scripts/init.py <name> --only ui [其它选项]`
3. 渲染 `templates/frontend/*`，替换变量
4. 复制到目标目录
5. 输出启动指引：`cd <project-name> && pnpm install && pnpm dev`

## 典型启动流程

```bash
cd my-web
pnpm install        # 或 npm install
pnpm dev            # 启动开发服务器
# 访问 http://localhost:5173
```

## 与其他命令的关系

- `/yz-init-ui <name>`：本 skill，纯前端
- `/yz-init-admin <name>`：完整前后端（详见 yz-init-admin skill）
- `/yz-init-server <name>`：后端 + 中间件（详见 yz-init-server skill）
