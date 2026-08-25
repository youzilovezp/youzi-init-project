/**
 * stores/user — token 持久化 + logout 清空 验证。
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'

describe('user store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('starts with empty token', () => {
    const store = useUserStore()
    expect(store.token).toBe('')
    expect(store.isLogin).toBe(false)
  })

  it('logout clears token and localStorage', async () => {
    const store = useUserStore()
    store.token = 'fake-jwt'
    localStorage.setItem('access_token', 'fake-jwt')
    await store.logout()
    expect(store.token).toBe('')
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('isLogin is true when token is set', () => {
    const store = useUserStore()
    store.token = 'fake-jwt'
    expect(store.isLogin).toBe(true)
  })
})
