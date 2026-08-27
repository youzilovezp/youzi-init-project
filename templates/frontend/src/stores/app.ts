import { defineStore } from 'pinia'
import { computed, watch, type Ref } from 'vue'
import { useDark, useStorage, type BasicColorSchema } from '@vueuse/core'

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
    const hex = (s: string): [number, number, number] => [
      parseInt(s.slice(1, 3), 16),
      parseInt(s.slice(3, 5), 16),
      parseInt(s.slice(5, 7), 16),
    ]
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
  // storageRef 用 flush:'sync' 的 useStorage：useDark 内部默认 'pre' 写入是微任务，同步断言读不到
  const themeStorage = useStorage<BasicColorSchema>(
    'youzi-app-theme',
    'auto',
    undefined,
    { flush: 'sync' },
  )
  const isDark = useDark({
    storageKey: 'youzi-app-theme',
    storageRef: computed({
      get: () => themeStorage.value,
      set: (v: BasicColorSchema) => {
        themeStorage.value = v
      },
    }) as Ref<BasicColorSchema>,
  })
  // useDark 内部 class 切换是 post-flush（微任务），补一个 sync watch 保证同步可见
  watch(
    isDark,
    (v) => {
      document.documentElement.classList.toggle('dark', v)
    },
    { immediate: true, flush: 'sync' },
  )
  const primaryColor = useStorage(
    'youzi-app-primary',
    THEME_PRESETS[0]?.color ?? '#f59e0b',
    undefined,
    { flush: 'sync' },
  )

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

  // 初始化 + 跟随变化应用变量（sync：测试与首帧同步可见）
  watch(primaryColor, applyPrimaryColor, { immediate: true, flush: 'sync' })

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
