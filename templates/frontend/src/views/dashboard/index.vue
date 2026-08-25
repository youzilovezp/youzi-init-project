<script setup lang="ts">
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
</script>

<template>
  <div class="dashboard">
    <el-card>
      <template #header>
        <span v-if="userStore.userInfo">欢迎回来，{{ userStore.displayName }}</span>
        <el-skeleton v-else :rows="1" animated />
      </template>
      <p>从这里开始：</p>
      <ul>
        <li>左侧菜单 → 用户管理 / 角色管理</li>
        <li>右上角头像 → 修改密码 / 退出登录</li>
        <li>需要排查接口？后端文档：<a href="/api/v1/docs" target="_blank">Swagger</a></li>
      </ul>
    </el-card>
  </div>
</template>
