# youzi-init-project 前端精装升级设计

日期：2026-08-27
状态：已与用户确认（路线：精装；TailwindCSS；暗色+主题色；不多标签页；Dashboard 卡片+图表）

## 背景与目标

`templates/frontend/`（Vue 3 + TS + Vite + Element Plus + Pinia）当前视觉为手写朴素样式：
深色硬编码侧边栏、纯文字 Dashboard、无暗色模式、无主题系统。目标是**不重复造轮子**，
全部采用业界标准方案升级视觉交互体验，同时**业务逻辑与测试零破坏**。

## 非目标（YAGNI）

多标签页、i18n、水印、全屏、vben-admin 全家桶、iconify、vxe-table、更换 UI 框架。

## 技术栈增量

| 新依赖 | 用途 |
|---|---|
| `tailwindcss` v4 + `@tailwindcss/vite` | 布局与自定义视觉（与 EP 共存） |
| `@vueuse/core` | `useDark`/`useStorage` 暗色持久化 |
| `echarts` + `vue-echarts` | Dashboard 图表 |

保留：Element Plus、@element-plus/icons-vue、pinia、axios、vue-router。

## 主题系统（零自研，全官方方案）

- **暗色**：引入 EP 官方 `element-plus/theme-chalk/dark/css-vars.css`；
  `useDark()` 写 `html.dark` class，localStorage 持久化，Tailwind `dark:` 变体绑定同名 class。
- **主题色**：预设色板（柚子橙 #f59e0b 品牌色 / 品牌蓝 #409eff / 紫罗兰 #7c3aed / 翡翠绿 #10b981 等），
  通过写 `--el-color-primary` 及 light-3/5/7/8/9、dark-2 全系 CSS 变量实现一键换色，localStorage 持久化。
- Tailwind v4 用 `@theme` 注册少量设计令牌（品牌色、卡片圆角），颜色引用 EP 变量，两套体系不冲突。

## 布局（BasicLayout.vue 重写）

- 侧边栏：背景/文字色全部走 CSS 变量（亮暗自适应），菜单高亮为圆角条样式（EP menu 支持）。
- 顶栏：毛玻璃（`backdrop-blur` + 半透明背景 + 底部细边框），左侧折叠按钮+面包屑，
  右侧工具组：暗色切换按钮（☀/🌙）、主题色 Popover 选板、用户下拉（头像+昵称）。
- 内容区：统一页面容器（圆角卡片 + 阴影 + 过渡动画），路由 fade/slide 切换动画保留。
- 菜单数据结构、权限过滤（isSuperuser）逻辑不变。

## 登录页

全屏品牌渐变背景 + CSS 装饰光斑（blur 圆），玻璃拟态登录卡（半透明白/黑 + backdrop-blur + 圆角+阴影），
标题走 APP_TITLE 配置，跟随暗色模式。表单校验、redirect 逻辑不变。

## Dashboard

- 顶部 4 张统计卡：用户总数 / 启用用户 / 角色数 /（第 4 张：当前登录用户欢迎或系统信息）。
  前三项调现有 `listUsers`/`listRoles` 接口取真实数据（listRoles 全量、listUsers 拉总数）。
- ECharts 折线图：近 7 日登录趋势（占位数据，代码中注明 `// 占位数据，接入真实日志后替换`）。
- ECharts 饼图：各角色用户数分布（真实数据：按角色统计用户列表）。
- 快捷入口卡：用户管理 / 角色管理 / Swagger 文档链接。
- 图表配色跟随主题色；暗色下文字/网格线用 EP 变量色。

## 用户/角色管理页

搜索区卡片化（圆角、间距、按钮组右对齐）、表格卡片化、分页右对齐；
操作列保留 link 按钮。业务逻辑（增删改查、校验、权限）零改动。
`add_module.py` 生成的业务页面沿用 `.page` 容器约定，新视觉自动生效——需保证 `.page` 类新样式兼容生成的页面结构。

## 状态与工具

- `stores/app.ts` 扩展：`isDark`、`primaryColor`（useStorage 持久化）+ 应用主题色变量的 action。
- 新增 `composables/use-theme.ts`（如实现中 judged 不必要可并入 app store——以最少文件为准）。

## 错误处理

主题恢复失败（localStorage 损坏）回退默认值；图表数据接口失败显示 EP Empty 占位。

## 测试与验证

1. 现有 vitest 测试（login-redirect、stores-user）保持绿。
2. 新增 app store 主题持久化测试（设置 isDark/primaryColor 后 localStorage 生效）。
3. `vue-tsc --noEmit && vite build` 通过。
4. 端到端目验：用模板生成真实项目，`make dev`，检查登录→布局→暗色切换→主题色切换→Dashboard→用户/角色 CRUD。
5. `scripts/add_module.py` 生成一个 order 模块，确认新页面在新视觉下正常。

## 交付物

全部改动落在 `templates/frontend/`（package.json、vite.config.ts、src/**），
模板 `.tmpl` 文档（前端说明/技术栈）同步更新依赖清单与主题说明。
