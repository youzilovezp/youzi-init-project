<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore, THEME_PRESETS } from '@/stores/app'
import { ElMessageBox } from 'element-plus'
import { Sunny, Moon } from '@element-plus/icons-vue'
import { APP_TITLE } from '@/config'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()

const menus = [
  { path: '/dashboard', title: '首页', icon: 'HomeFilled' },
  {
    title: '系统管理',
    icon: 'Setting',
    children: [
      { path: '/system/user', title: '用户管理', icon: 'User', admin: true },
      { path: '/system/role', title: '角色管理', icon: 'UserFilled', admin: true },
    ],
  },
]

const filteredMenus = computed(() => {
  return menus
    .map((m) => {
      if (m.children) {
        const children = m.children.filter(
          (c) => !c.admin || userStore.isSuperuser
        )
        return children.length ? { ...m, children } : null
      }
      return m
    })
    .filter((m): m is NonNullable<typeof m> => m !== null)
})

const activeMenu = computed(() => route.path)

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      type: 'warning',
    })
    await userStore.logout()
    // replace 而非 push：避免在历史栈留一条已退出的回边
    router.replace('/login')
  } catch {
    /* cancel */
  }
}
</script>

<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="appStore.sidebarCollapsed ? '64px' : '220px'" class="layout-aside bg-bg-card">
      <div class="logo">
        <img src="/youzi-logo.svg" alt="logo" class="logo-img" />
        <span v-if="!appStore.sidebarCollapsed" class="logo-text text-text">{{ APP_TITLE }}</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="appStore.sidebarCollapsed"
        :collapse-transition="false"
        router
      >
        <template v-for="menu in filteredMenus" :key="menu.path">
          <el-sub-menu v-if="menu.children" :index="menu.path || menu.title">
            <template #title>
              <el-icon><component :is="menu.icon" /></el-icon>
              <span>{{ menu.title }}</span>
            </template>
            <el-menu-item v-for="child in menu.children" :key="child.path" :index="child.path">
              <el-icon><component :is="child.icon" /></el-icon>
              <template #title>{{ child.title }}</template>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="menu.path">
            <el-icon><component :is="menu.icon" /></el-icon>
            <template #title>{{ menu.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶栏：毛玻璃 -->
      <el-header height="56px" class="layout-header bg-bg-card/70 backdrop-blur-md border-b border-border">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="appStore.toggleSidebar">
            <component :is="appStore.sidebarCollapsed ? 'Expand' : 'Fold'" />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <!-- 暗色切换 -->
          <el-button circle :title="appStore.isDark ? '切换亮色模式' : '切换暗色模式'" @click="appStore.toggleDark">
            <el-icon><Moon v-if="appStore.isDark" /><Sunny v-else /></el-icon>
          </el-button>

          <!-- 主题色 -->
          <el-popover :width="220" trigger="click" placement="bottom-end">
            <template #reference>
              <el-button circle title="主题色">
                <span class="primary-dot" :style="{ background: appStore.primaryColor }" />
              </el-button>
            </template>
            <div class="swatch-grid">
              <div v-for="p in THEME_PRESETS" :key="p.color" class="swatch-item">
                <button
                  type="button"
                  class="swatch"
                  :class="{ active: p.color === appStore.primaryColor }"
                  :style="{ background: p.color }"
                  :title="p.name"
                  @click="appStore.setPrimaryColor(p.color)"
                />
                <span class="swatch-name">{{ p.name }}</span>
              </div>
            </div>
          </el-popover>

          <!-- 用户 -->
          <el-dropdown @command="(c: string) => c === 'logout' && handleLogout()">
            <span class="user-info">
              <el-avatar :size="32">{{ userStore.userInfo?.nickname?.charAt(0) || 'U' }}</el-avatar>
              <span>{{ userStore.displayName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容 -->
      <el-main class="layout-main bg-bg-page">
        <router-view v-slot="{ Component }">
          <transition name="fade">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped lang="scss">
.layout-container {
  height: 100vh;
}

.layout-aside {
  transition: width 0.3s;
  overflow-x: hidden;

  .logo {
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    padding: 0 16px;
    gap: 8px;
    font-size: 16px;
    font-weight: bold;
    border-bottom: 1px solid var(--el-border-color-light);
    overflow: hidden;
  }

  .logo-img {
    height: 36px;
    width: 36px;
    flex-shrink: 0;
  }

  .logo-text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  :deep(.el-menu) {
    border-right: none;
  }
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .collapse-btn {
      font-size: 20px;
      cursor: pointer;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.primary-dot {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
}

.swatch-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px 8px;
}

.swatch-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.swatch {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  padding: 0;
  cursor: pointer;
  transition: transform 0.15s;

  &:hover {
    transform: scale(1.15);
  }

  &.active {
    box-shadow:
      0 0 0 2px var(--el-bg-color-overlay),
      0 0 0 4px var(--el-color-primary);
  }
}

.swatch-name {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.layout-main {
  padding: 16px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
