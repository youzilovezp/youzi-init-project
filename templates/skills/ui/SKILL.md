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

随后 Claude 会询问项目显示名（可选），其余参数走默认值。确认后自动生成。

## 默认配置

| 项目     | 默认值                           |
| -------- | -------------------------------- |
| 前端框架 | Vue 3 + TS + Vite + Element Plus |
| 前端端口 | 3000                             |
| 后端 API | http://localhost:8000（代理）    |

## 输出结构

```
my-web/
├── src/
│   ├── api/                   # 接口层（Axios 拦截器）
│   ├── components/
│   ├── config/
│   ├── layouts/               # BasicLayout 等
│   ├── router/                # 路由 + 全局守卫
│   ├── stores/                # Pinia
│   ├── views/                 # 页面（dashboard / system / login / error）
│   ├── styles/
│   ├── types/
│   ├── utils/
│   ├── App.vue
│   └── main.ts
├── public/                    # 静态资源（含 favicon.svg）
├── docs/                      # 架构/技术栈/配置/开发文档
├── .env.development
├── .env.production
├── package.json
├── vite.config.ts
├── tsconfig.json
└── 前端说明.md
```

## 启动流程

```bash
cd my-web
pnpm install        # 或 npm install
pnpm dev            # 启动开发服务器
# 访问 http://localhost:3000
```

## 与其他命令的关系

- `/yz-init-ui <name>`：本技能，纯前端
- `/yz-init-admin <name>`：完整前后端
- `/yz-init-server <name>`：后端 + 中间件
