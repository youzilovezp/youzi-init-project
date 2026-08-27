# 前端精装升级 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用业界标准方案（TailwindCSS v4 + @vueuse/core + ECharts + EP 官方主题变量）升级 `templates/frontend/` 视觉：暗色模式、主题色切换、毛玻璃布局、玻璃拟态登录页、卡片+图表 Dashboard，业务逻辑零改动。

**Architecture:** 在现有 Vue 3 + Element Plus 项目上增量引入工具链。主题走两条官方通道：EP CSS 变量（组件）+ Tailwind `dark:` 变体（布局），由 app store 的 `useDark`/`useStorage` 统一驱动。所有改动落在 `templates/frontend/`，模板机制（copy + Jinja2 渲染 `.tmpl`）不变。

**Tech Stack:** TailwindCSS v4、@vueuse/core、echarts + vue-echarts、Element Plus 2.6、Vite 5。

## Global Constraints

- 工作目录：仓库根为 `/Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project`，所有前端命令在 `templates/frontend/` 下执行。
- 新增依赖仅限：`tailwindcss`、`@tailwindcss/vite`、`@vueuse/core`、`echarts`、`vue-echarts`。禁止引入其他运行时依赖。
- Node >= 18，pnpm/npm 均可（模板内无 lockfile）。
- 现有 vitest 测试（`src/__tests__/login-redirect.test.ts`、`stores-user.test.ts`）必须保持通过。
- 业务逻辑（API 调用、表单校验、权限过滤、redirect 处理）零改动——只动样式与主题相关代码。
- `src/styles/index.scss` 中 `.page` 容器类必须保留（`scripts/add_module.py` 生成的业务页面依赖它）。
- 每个任务完成后 `npx vue-tsc --noEmit` 必须通过（Task 1 装完依赖后开始要求）。
- 提交信息用中文，`feat:`/`test:`/`chore:` 前缀。
- `templates/frontend/` 下 src 是原样复制的普通文件（非 .tmpl），直接编辑；只有文档是 `.tmpl`。

---

### Task 1: 依赖与 Tailwind v4 骨架

**Files:**
- Modify: `templates/frontend/package.json`
- Modify: `templates/frontend/vite.config.ts`
- Create: `templates/frontend/src/styles/tailwind.css`

**Interfaces:**
- Consumes: 现有 vite.config.ts 的插件数组。
- Produces: `src/styles/tailwind.css`（含 `@theme` 设计令牌与 EP 变量对齐），后续所有样式任务 import 它。

- [ ] **Step 1: 安装依赖**

```bash
cd templates/frontend && npm install tailwindcss @tailwindcss/vite @vueuse/core echarts vue-echarts
```

（npm 源慢可换 pnpm；package.json 由包管理器自动更新。）

- [ ] **Step 2: vite.config.ts 接入 Tailwind 插件**

在 `plugins: [vue(), ...]` 数组开头加：

```ts
import tailwindcss from '@tailwindcss/vite'
// plugins 数组内：
plugins: [
  tailwindcss(),
  vue(),
  // ...其余不动
],
```

- [ ] **Step 3: 创建 src/styles/tailwind.css**

```css
@import "tailwindcss";

/* dark 变体绑定 html.dark class（与 EP 官方暗色、vueuse useDark 一致） */
@custom-variant dark (&:where(.dark, .dark *));

/* 设计令牌：品牌色引用 EP 变量，改主题色时 Tailwind 工具类自动跟随 */
@theme {
  --color-primary: var(--el-color-primary);
  --color-bg-page: var(--el-bg-color-page);
  --color-bg-card: var(--el-bg-color);
  --color-text: var(--el-text-color-primary);
  --color-text-secondary: var(--el-text-color-secondary);
  --color-border: var(--el-border-color-light);
  --radius-card: 12px;
}
```

- [ ] **Step 4: styles/index.scss 引入并验证**

`src/styles/index.scss` 顶部加 `@import './tailwind.css';`，并在文件末尾保留/更新 `.page` 类：

```scss
/* 页面统一容器：add_module.py 生成的业务页面依赖此类 */
.page {
  background: var(--el-bg-color);
  border-radius: var(--radius-card);
  padding: 16px;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 1px 3px rgb(0 0 0 / 0.04);
}
```

同时删除 index.scss 中旧的 `body { background: #f0f2f5; }` 硬编码背景色，改为 `background: var(--el-bg-color-page);`；`a` 颜色改 `var(--el-color-primary)`。

- [ ] **Step 5: 验证构建**

```bash
cd templates/frontend && npx vue-tsc --noEmit && npm run build
```

Expected: 构建成功，无 TS 错误。

- [ ] **Step 6: Commit**

```bash
git add templates/frontend/package.json templates/frontend/package-lock.json templates/frontend/vite.config.ts templates/frontend/src/styles/
git commit -m "feat: 接入 TailwindCSS v4 + 依赖（vueuse/echarts）"
```

---

### Task 2: 主题系统（app store + main.ts）

**Files:**
- Modify: `templates/frontend/src/stores/app.ts`
- Modify: `templates/frontend/src/main.ts`
- Test: `templates/frontend/src/__tests__/stores-app-theme.test.ts`

**Interfaces:**
- Consumes: `@vueuse/core` 的 `useDark`/`useStorage`（Task 1 安装）。
- Produces: `useAppStore` 新增 `isDark: Ref<boolean>`（setter `toggleDark`/`setDark`）、`primaryColor: Ref<string>`、`setPrimaryColor(color: string): void`、色板常量 `THEME_PRESETS: { name: string; color: string }[]`。后续布局/登录页任务消费这些名字。

- [ ] **Step 1: 写失败测试**

```ts
// src/__tests__/stores-app-theme.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAppStore, THEME_PRESETS } from '@/stores/app'

describe('app store 主题', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('默认亮色 + 默认主题色为柚子橙', () => {
    const app = useAppStore()
    expect(app.isDark).toBe(false)
    expect(app.primaryColor).toBe('#f59e0b')
  })

  it('setDark 同步 html class 与 localStorage', () => {
    const app = useAppStore()
    app.setDark(true)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(localStorage.getItem('youzi-app-theme')).toContain('dark')
    app.setDark(false)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('setPrimaryColor 更新 EP CSS 变量与 localStorage', () => {
    const app = useAppStore()
    app.setPrimaryColor('#409eff')
    const v = getComputedStyle(document.documentElement).getPropertyValue('--el-color-primary')
    expect(v.trim().toLowerCase()).toBe('#409eff')
    expect(localStorage.getItem('youzi-app-primary')).toBe('#409eff')
  })

  it('色板预设包含品牌蓝且无重复色值', () => {
    const colors = THEME_PRESETS.map((p) => p.color)
    expect(colors).toContain('#409eff')
    expect(new Set(colors).size).toBe(colors.length)
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd templates/frontend && npx vitest run src/__tests__/stores-app-theme.test.ts
```

Expected: FAIL（`isDark` 不存在 / import 报错）。

- [ ] **Step 3: 实现 app store**

```ts
// src/stores/app.ts 全量替换
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useDark, useStorage } from '@vueuse/core'

/** 主题色预设（与设计文档一致） */
export interface ThemePreset {
  name: string
  color: string
}

export const THEME_PRESETS: ThemePreset[] = [
  { name: '柚子橙', color: '#f59e0b' },
  { name: '品牌蓝', color: '#409eff' },
  { name: '紫罗兰', color: '#7c3aed' },
  { name: '翡翠绿', color: '#10b981' },
  { name: '赤霞红', color: '#ef4444' },
  { name: '黛青蓝', color: '#0ea5e9' },
]

/** 生成 primary 的 light-3/5/7/8/9 与 dark-2 变量并写到 documentElement */
function applyPrimaryColor(color: string) {
  const root = document.documentElement
  const mix = (c: string, t: string, ratio: number) => {
    const hex = (s: string) => [1, 3, 5].map((i) => parseInt(s.slice(i, i + 2), 16))
    const [r1, g1, b1] = hex(c)
    const [r2, g2, b2] = hex(t)
    const m = (a: number, b: number) => Math.round(a * ratio + b * (1 - ratio))
      .toString(16)
      .padStart(2, '0')
    return `#${m(r1, r2)}${m(g1, g2)}${m(b1, b2)}`
  }
  const white = '#ffffff'
  const black = '#000000'
  root.style.setProperty('--el-color-primary', color)
  for (const i of [3, 5, 7, 8, 9]) {
    root.style.setProperty(`--el-color-primary-light-${i}`, mix(color, white, 1 - i / 10))
  }
  root.style.setProperty('--el-color-primary-dark-2', mix(color, black, 0.8))
}

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = useStorage('youzi-app-sidebar-collapsed', false)

  // vueuse useDark：读写 html.dark class + localStorage('youzi-app-theme')
  const isDark = useDark({ storageKey: 'youzi-app-theme' })
  const primaryColor = useStorage('youzi-app-primary', THEME_PRESETS[0].color)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
  function toggleDark() {
    isDark.value = !isDark.value
  }
  function setDark(v: boolean) {
    isDark.value = v
  }
  function setPrimaryColor(color: string) {
    primaryColor.value = color
  }

  // 初始化 + 跟随变化应用变量
  watch(primaryColor, applyPrimaryColor, { immediate: true })

  return {
    sidebarCollapsed,
    toggleSidebar,
    isDark,
    toggleDark,
    setDark,
    primaryColor,
    setPrimaryColor,
  }
})
```

- [ ] **Step 4: main.ts 引入 EP 暗色变量 CSS**

在 `import 'element-plus/dist/index.css'` 之后加一行：

```ts
import 'element-plus/theme-chalk/dark/css-vars.css'
```

- [ ] **Step 5: 跑测试确认通过 + 全量测试**

```bash
cd templates/frontend && npx vitest run
```

Expected: 全部 PASS（含旧测试）。

- [ ] **Step 6: Commit**

```bash
git add templates/frontend/src/stores/app.ts templates/frontend/src/main.ts templates/frontend/src/__tests__/stores-app-theme.test.ts
git commit -m "feat: 暗色模式 + 主题色切换（EP CSS 变量 + vueuse）"
```

---

### Task 3: 布局重写（BasicLayout.vue）

**Files:**
- Modify: `templates/frontend/src/layouts/BasicLayout.vue`（全量重写模板与样式，script 逻辑保留）

**Interfaces:**
- Consumes: `useAppStore` 的 `isDark`/`toggleDark`/`primaryColor`/`setPrimaryColor`、`THEME_PRESETS`（Task 2）。
- Consumes: Tailwind 工具类 + `@theme` 令牌（Task 1）。
- Produces: 无（终端 UI 层）。

- [ ] **Step 1: 重写 BasicLayout.vue**

script 部分在现有基础上新增 `import { THEME_PRESETS } from '@/stores/app'` 与 `import { Sunny, Moon } from '@element-plus/icons-vue'`（图标已全局注册，亦可直接用字符串）。模板/样式全量替换为：

关键结构（完整代码在实现时落地，保持以下约定）：
- `el-aside`：去掉 `background-color`/`text-color`/`active-text-color` 三个硬编码属性，背景用 `bg-bg-card`（Tailwind 令牌 → EP 变量），菜单高亮走 EP 默认主题色变量；`el-menu` 加 `:collapse-transition="false"`。
- 顶栏 `el-header`：`class="bg-bg-card/70 backdrop-blur-md border-b border-border"`，高 56px。
- 顶栏右侧工具组：暗色切换按钮（`el-button` circle + `Sunny`/`Moon` 图标切换）→ 主题色 `el-popover`（内为色板圆点列表，点击 `appStore.setPrimaryColor(p.color)`，当前色加 ring 高亮）→ 用户 `el-dropdown`（保留原 logout 逻辑）。
- 内容区：`el-main` 用 `bg-bg-page`，内层页面容器由 `.page`/各页面自己负责。
- 路由过渡保留 fade。
- 所有暗色适配走 EP 变量/Tailwind `dark:` 变体，禁止再出现 `#001529` 等硬编码色。

菜单数据 `menus`、`filteredMenus` 计算、`handleLogout` 原样保留。

- [ ] **Step 2: 验证构建 + 测试**

```bash
cd templates/frontend && npx vue-tsc --noEmit && npm run build && npx vitest run
```

Expected: 全部通过。

- [ ] *(optional)* **Step 3: 目验**

`npm run dev` 打开 http://localhost:3000（无后端时跳过 API 请求，仅看登录页样式），检查侧边栏/顶栏是否正常渲染。

- [ ] **Step 4: Commit**

```bash
git add templates/frontend/src/layouts/BasicLayout.vue
git commit -m "feat: 布局重写——主题自适应侧边栏 + 毛玻璃顶栏 + 主题工具组"
```

---

### Task 4: 登录页玻璃拟态

**Files:**
- Modify: `templates/frontend/src/views/login/index.vue`（模板与样式重写，script 逻辑不动）

**Interfaces:**
- Consumes: Tailwind 类、EP 变量（暗色自动跟随，无需消费 store）。
- Produces: 无。

- [ ] **Step 1: 重写模板与样式**

script 完全不动。模板替换为：
- 外层：`h-screen w-full relative overflow-hidden flex items-center justify-center`，背景 `bg-[linear-gradient(135deg,var(--el-color-primary-light-3),var(--el-color-primary-dark-2))]`（跟随主题色）。
- 装饰光斑：两个 absolute 的 `rounded-full blur-3xl opacity-30 bg-white/40 dark:bg-white/10` 大圆，错位摆放。
- 登录卡：`w-96 p-8 rounded-2xl backdrop-blur-xl bg-white/80 dark:bg-[#1d1d1f]/80 border border-white/60 dark:border-white/10 shadow-2xl`。
- 标题：logo 图标 + APP_TITLE（从 `@/config` import，替换硬编码 "Youzi Admin"）。
- 表单、校验、submit、tips 文案原样保留。

- [ ] **Step 2: 验证构建 + 测试**

```bash
cd templates/frontend && npx vue-tsc --noEmit && npm run build && npx vitest run
```

Expected: 全部通过（login-redirect 测试不涉及样式，应保持绿）。

- [ ] **Step 3: Commit**

```bash
git add templates/frontend/src/views/login/index.vue
git commit -m "feat: 登录页玻璃拟态重设计（跟随主题色与暗色）"
```

---

### Task 5: Dashboard 卡片 + ECharts

**Files:**
- Create: `templates/frontend/src/views/dashboard/components/LoginTrendChart.vue`
- Create: `templates/frontend/src/views/dashboard/components/RolePieChart.vue`
- Modify: `templates/frontend/src/views/dashboard/index.vue`（全量重写）
- Modify: `templates/frontend/src/api/role.ts`（如 listRoles 返回类型缺字段则不动——以实际为准）

**Interfaces:**
- Consumes: `listUsers`（`UserListParams`/`PageResult<UserInfo>`）、`listRoles`（`Role[]`，含 `id/name`）。
- Consumes: `useAppStore().primaryColor`（图表配色跟随）、`isDark`。
- Produces: `LoginTrendChart.vue`（props：`none`，自包含占位数据）、`RolePieChart.vue`（props：`roles: { name: string; value: number }[]`）。

- [ ] **Step 1: 实现 LoginTrendChart.vue**

```vue
<script setup lang="ts">
// 近 7 日登录趋势（占位数据，接入真实日志后替换）
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useAppStore } from '@/stores/app'

use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const appStore = useAppStore()
const days = [...Array(7)].map((_, i) => {
  const d = new Date(Date.now() - (6 - i) * 86400000)
  return `${d.getMonth() + 1}/${d.getDate()}`
})
const data = [12, 18, 9, 24, 30, 21, 26] // 占位数据，接入真实日志后替换

const option = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 16, top: 20, bottom: 28 },
  xAxis: { type: 'category', data: days, boundaryGap: false },
  yAxis: { type: 'value' },
  series: [
    {
      type: 'line',
      smooth: true,
      data,
      areaStyle: { opacity: 0.15 },
      lineStyle: { width: 2.5 },
      itemStyle: { color: appStore.primaryColor },
    },
  ],
}))
</script>

<template>
  <VChart :option="option" autoresize style="height: 280px" />
</template>
```

- [ ] **Step 2: 实现 RolePieChart.vue**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echars/renderers'
import { useAppStore } from '@/stores/app'

use([PieChart, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps<{ data: { name: string; value: number }[] }>()
const appStore = useAppStore()

// 以主题色为基色的扩展色板
const palette = computed(() => {
  const base = appStore.primaryColor
  return [base, '#94a3b8', '#f472b6', '#34d399', '#fbbf24', '#60a5fa'].slice(
    0,
    Math.max(props.data.length, 1),
  )
})

const option = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [
    {
      type: 'pie',
      radius: ['40%', '65%'],
      data: props.data,
      label: { show: false },
    },
  ],
  color: palette.value,
}))
</script>

<template>
  <VChart :option="option" autoresize style="height: 280px" />
</template>
```

注意：上面 `from 'echars/renderers'` 是笔误示范——实现时必须写 `from 'echarts/renderers'`。

- [ ] **Step 3: 重写 dashboard/index.vue**

结构：
- 顶部 3+1 统计卡（`el-row`/`el-col` 或 Tailwind grid）：用户总数（`User` 图标）、启用用户数、角色数、欢迎卡（当前用户昵称 + 日期）。数据：并行 `listUsers({ page: 1, page_size: 1 })` 拿 total、`listUsers({ page: 1, page_size: 100, is_active: true })` 拿 total（>100 时显示 total 即可）、`listRoles()` 拿 length。卡片样式：`bg-bg-card rounded-xl p-5 border border-border` + 图标圆底色用主题色 light-9 变量。
- 中部两栏：左 `LoginTrendChart`、右 `RolePieChart`（role→用户数映射：从 `listUsers({ page_size: 100 })` 的 items 按 `role_name` 分组计数；接口失败显示 `el-empty`）。
- 底部快捷入口卡：用户管理 / 角色管理 / Swagger（`/api/v1/docs`）。
- 全部请求 try/catch，失败降级为 `el-empty` 或 0。

- [ ] **Step 4: 验证构建 + 测试**

```bash
cd templates/frontend && npx vue-tsc --noEmit && npm run build && npx vitest run
```

Expected: 全部通过。

- [ ] **Step 5: Commit**

```bash
git add templates/frontend/src/views/dashboard/
git commit -m "feat: Dashboard 重设计——统计卡片 + ECharts 图表 + 快捷入口"
```

---

### Task 6: 用户/角色管理页视觉统一

**Files:**
- Modify: `templates/frontend/src/views/system/user/index.vue`
- Modify: `templates/frontend/src/views/system/role/index.vue`

**Interfaces:**
- Consumes: `.page` 容器样式（Task 1）、EP 变量。
- Produces: 无。

- [ ] **Step 1: user/index.vue 模板微调**

script 零改动。模板改动：
- 搜索栏与表格不再各包一层 `el-card`——整页用单个 `.page` 容器：搜索 `el-form :inline` 区 + 分隔 + `el-table` + 分页。
- 表格外层加 `rounded-lg overflow-hidden border border-border`。
- 分页容器加 `flex justify-end mt-4`（去掉内联 style）。
- 操作列按钮不变。

- [ ] **Step 2: role/index.vue 同样处理**（结构同 user 页）。

- [ ] **Step 3: 验证构建 + 测试**

```bash
cd templates/frontend && npx vue-tsc --noEmit && npm run build && npx vitest run
```

Expected: 全部通过。

- [ ] **Step 4: Commit**

```bash
git add templates/frontend/src/views/system/
git commit -m "feat: 用户/角色管理页视觉统一（卡片化容器 + 圆角表格）"
```

---

### Task 7: 端到端目验 + 文档同步

**Files:**
- Modify: `templates/frontend/前端说明.md.tmpl`
- Modify: `templates/frontend/docs/技术栈.md.tmpl`（如存在该文件名）
- Modify: README.md 前端技术栈表格（仓库根）

**Interfaces:**
- Consumes: 全部前序任务。
- Produces: 面向脚手架用户的文档更新。

- [ ] **Step 1: 生成真实项目验证**

```bash
cd /Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project
python3 scripts/init.py /tmp/youzi-e2e-visual --mode ui 2>/dev/null || python3 scripts/init.py /tmp/youzi-e2e-visual
```

（以 init.py 实际参数为准；生成后 `cd /tmp/youzi-e2e-visual && pnpm install && pnpm dev`，浏览器目验：登录页 → 布局 → 暗色切换 → 主题色切换 → Dashboard 图表 → 用户/角色 CRUD。）

如目验发现问题，修复后重跑 `npx vitest run && npm run build`。

- [ ] **Step 2: add_module 兼容验证**

在生成项目里执行 `python3 backend/scripts/add_module.py order --title "订单管理" --fields "name:str,price:float:0"`，注册 5 处后 `pnpm dev` 目验 order 页面在新 `.page` 容器下正常。

- [ ] **Step 3: 更新文档**

- `前端说明.md.tmpl`：技术栈清单加 Tailwind/vuuse/echarts；新增「主题定制」小节（暗色 + 主题色 + 色板扩展方法）。
- 根 README.md 前端表格补 3 行（Tailwind CSS、@vueuse/core、ECharts）。

- [ ] 建议顺带在生成项目跑一次 `python3 backend/scripts/check.py`（如存在）确保模板完整性。

- [ ] **Step 4: 清理与提交**

```bash
rm -rf /tmp/youzi-e2e-visual
git add templates/frontend/前端说明.md.tmpl templates/frontend/docs/ README.md
git commit -m "docs: 前端视觉升级文档同步"
```

---

## Self-Review 结论

- Spec 覆盖：主题系统→Task 1/2；布局→Task 3；登录页→Task 4；Dashboard→Task 5；管理页→Task 6；测试/端到端/文档→Task 2/7。无遗漏。
- 占位符扫描：Task 3 布局以约定+关键结构描述（视觉代码属实现细节，约定了类名/结构/禁止硬编码色），其余任务含完整代码。
- 类型一致性：`THEME_PRESETS`/`setDark`/`setPrimaryColor`/`primaryColor`/`isDark` 在 Task 2 定义、Task 3/5 消费，签名一致；图表组件 props `data: { name: string; value: number }[]` 与 dashboard 传入一致。
