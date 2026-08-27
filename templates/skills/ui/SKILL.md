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

**端口动态避让（必读）**：3000 被占用时 vite 自动改用 3001/3002 并打印提示。
启动后必须以 vite 输出的 `Local:` 实际地址为准告知用户；
若怀疑用户浏览器停在旧页面（改版后仍显示旧样式），让用户 Cmd+Shift+R 强制刷新。

## 前端 UI 生态硬约束（生成与后续迭代均生效）

本脚手架前端**严格遵守 Naive UI 全套生态**，AI 生成/修改页面时不得偏离：

1. **组件库唯一**：只允许 `naive-ui`（unplugin-vue-components + NaiveUiResolver 按需自动导入）。
   禁止引入 Element Plus、Ant Design Vue、Vuetify 等任何其他组件库，禁止出现 `el-*` / `a-*` 标签。
2. **图标唯一**：只用 `@vicons`（xicons 生态，Naive UI 官方推荐），当前用 `@vicons/ionicons5`，
   必须通过 `<n-icon :component="Xxx">` 渲染；禁止 font-awesome / heroicons / element-icons 等。
3. **主题定制**：走 `n-config-provider` 的 `themeOverrides`（JS 侧）+ `--yz-*` CSS 设计令牌；
   禁止用深层选择器覆盖 Naive 组件内部 class。
4. **Tailwind 定位**：仅作布局/间距原子类辅助；视觉主题一律走上面两条。
   **Tailwind 入口必须在 `main.ts` 直连 `import './styles/tailwind.css'`，禁止从 SCSS `@import` 内联
   （SCSS 内联会使 `@import "tailwindcss"` 指令失效，工具类全部丢失）。**
5. **参考资源**：组件用法查 https://www.naiveui.com/zh-CN/os-theme/docs/introduction ；
   图标查 xicons（https://github.com/07akioni/xicons ）；视觉规范对齐 NaiveUI 官方设计稿。

## 与其他命令的关系

- `/yz-init-admin <name>`：完整前后端
- `/yz-init-server <name>`：后端 + 中间件
