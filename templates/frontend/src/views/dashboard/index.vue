<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useUserStore } from '@/stores/user'
import request from '@/api/request'

const userStore = useUserStore()

// 接入真实统计 endpoint。占位符仅展示，endpoint 不存在时显示 0。
const stats = ref({
  totalUsers: 0,
  todayActive: 0,
  totalRoles: 0,
})

async function loadStats() {
  try {
    const data = await request.get<typeof stats.value, typeof stats.value>('/stats/overview', { silent: true })
    if (data && typeof data === 'object') {
      stats.value = data as typeof stats.value
    }
  } catch {
    // 静默失败：endpoint 临时不可用时保持 0，不弹全局错误
  }
}

onMounted(() => {
  if (userStore.isLogin) loadStats()
})
</script>

<template>
  <div class="dashboard">
    <el-card>
      <template #header>
        <span>欢迎回来，{{ userStore.displayName }}</span>
      </template>
      <p>你可以：</p>
      <ul>
        <li>在左侧菜单中进入「用户管理」「角色管理」</li>
        <li>在右上角下拉菜单中退出登录</li>
        <li>查看后端 API 文档：<a href="/api/v1/docs" target="_blank">Swagger</a></li>
      </ul>
    </el-card>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="8">
        <el-card>
          <template #header><span>总用户数</span></template>
          <div class="metric">{{ stats.totalUsers }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>今日活跃</span></template>
          <div class="metric">{{ stats.todayActive }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>角色数量</span></template>
          <div class="metric">{{ stats.totalRoles }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped lang="scss">
.dashboard {
  :deep(.el-card) {
    margin-bottom: 16px;
  }
  .metric {
    font-size: 32px;
    font-weight: bold;
    color: #1890ff;
    text-align: center;
    padding: 16px 0;
  }
}
</style>
