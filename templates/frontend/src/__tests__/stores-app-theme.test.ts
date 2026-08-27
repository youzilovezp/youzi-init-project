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

  it('暗色下 light-3 改与暗色底混合（区别于亮色白混结果）', () => {
    const app = useAppStore()
    app.setDark(false)
    const light3 = getComputedStyle(document.documentElement)
      .getPropertyValue('--el-color-primary-light-3')
      .trim()
      .toLowerCase()
    app.setDark(true)
    const dark3 = getComputedStyle(document.documentElement)
      .getPropertyValue('--el-color-primary-light-3')
      .trim()
      .toLowerCase()
    expect(light3).toBe('#f8bb54')
    expect(dark3).toBe('#b2750e')
    expect(dark3).not.toBe(light3)
  })
})
