/**
 * Axios 实例 + 拦截器。
 *
 * - 请求拦截：自动注入 token
 * - 响应拦截：统一处理 code、错误提示
 * - 错误处理：401 自动跳登录页
 */
import axios, { AxiosError, type AxiosRequestConfig, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ApiResponse } from './types'

export interface RequestOptions extends AxiosRequestConfig {
  /** 静默模式：不显示全局错误提示 */
  silent?: boolean
}

// 让 axios 的 get/post/put/delete 都接受 silent 字段
declare module 'axios' {
  export interface AxiosRequestConfig {
    silent?: boolean
  }
}

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const TOKEN_KEY = import.meta.env.VITE_TOKEN_KEY || 'access_token'

// 单例化 401 弹窗，避免并发请求触发多个 ElMessageBox 堆叠
let authDialogShown = false
function showUnauthorizedDialog() {
  if (authDialogShown) return
  authDialogShown = true
  ElMessageBox.confirm('登录已过期，请重新登录', '提示', {
    confirmButtonText: '重新登录',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      localStorage.removeItem(TOKEN_KEY)
      window.location.href = '/login'
    })
    .catch(() => {
      // 用户取消，重置标记以便下次还能弹
    })
    .finally(() => {
      authDialogShown = false
    })
}

const request = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ---------- 请求拦截 ----------
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ---------- 响应拦截 ----------
request.interceptors.response.use(
  (response) => {
    const data = response.data as ApiResponse
    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code === 0) {
        return data.data
      }
      // 静默模式（silent=true）下不弹全局错误
      const silent = (response.config as RequestOptions).silent
      if (!silent) {
        ElMessage.error(data.message || '请求失败')
      }
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    return response.data
  },
  async (error: AxiosError<ApiResponse>) => {
    const silent = (error.config as RequestOptions | undefined)?.silent
    const status = error.response?.status
    const message = error.response?.data?.message || error.message || '网络异常'

    if (status === 401) {
      showUnauthorizedDialog()
      return Promise.reject(new Error('未授权'))
    }

    if (!silent) {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  }
)

export interface RequestOptionsExt extends AxiosRequestConfig {
  /** 静默模式：不显示全局错误提示 */
  silent?: boolean
}

export default request
