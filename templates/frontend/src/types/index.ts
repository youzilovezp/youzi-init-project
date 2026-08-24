// 全局类型声明
// 注：vite/client 已提供 *.vue / *.svg / *.png 等资源模块声明，无需重复
// 这里只补充项目自定义的 VITE_* 环境变量类型

interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_API_BASE_URL: string
  readonly VITE_TOKEN_KEY?: string
  readonly VITE_PROXY_TARGET?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
