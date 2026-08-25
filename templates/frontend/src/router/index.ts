// 路由配置
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/',
    component: () => import('@/layouts/BasicLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '首页', icon: 'HomeFilled' },
      },
      {
        path: 'system/user',
        name: 'SystemUser',
        component: () => import('@/views/system/user/index.vue'),
        meta: { title: '用户管理', icon: 'User', requiresAdmin: true },
      },
      {
        path: 'system/role',
        name: 'SystemRole',
        component: () => import('@/views/system/role/index.vue'),
        meta: { title: '角色管理', icon: 'UserFilled', requiresAdmin: true },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: { public: true, title: '404' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ---------- 全局守卫 ----------
router.beforeEach(async (to, _from, next) => {
  const userStore = useUserStore()

  // 设置页面标题
  const title = (to.meta.title as string) || ''
  document.title = title ? `${title} - ${import.meta.env.VITE_APP_TITLE}` : import.meta.env.VITE_APP_TITLE

  // 公开页面
  if (to.meta.public) {
    return next()
  }

  // 需要登录
  if (!userStore.isLogin) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }

  // 已登录但未拉取用户信息
  if (!userStore.userInfo) {
    try {
      await userStore.fetchProfile()
    } catch (e) {
      await userStore.logout()
      // 修复：刷新受保护路由时丢 redirect，导致登录后被送到默认页
      return next({ name: 'Login', query: { redirect: to.fullPath } })
    }
  }

  // 需要管理员
  if (to.meta.requiresAdmin && !userStore.isSuperuser) {
    return next({ name: 'Dashboard' })
  }

  next()
})

export default router
