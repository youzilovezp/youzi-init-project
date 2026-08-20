<script setup lang="ts">
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
</script>

<template>
  <div class="dashboard">
    <el-card>
      <template #header>
        <span>欢迎回来，{{ userStore.displayName }}</span>
      </template>
      <p>这里是仪表盘首页，你可以：</p>
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
          <div class="metric">--</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>今日活跃</span></template>
          <div class="metric">--</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header><span>角色数量</span></template>
          <div class="metric">--</div>
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
