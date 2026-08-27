<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { sanitizeRedirect } from '@/utils/redirect'
import { APP_TITLE } from '@/config'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '长度 3-50 个字符', trigger: 'blur' },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// 修复：已登录用户访问 /login 应自动跳走，否则会再次提交无效登录请求
onMounted(() => {
  if (userStore.isLogin) {
    router.replace('/dashboard')
  }
})

async function onSubmit() {
  if (!formRef.value) return
  // validate() 返回 Promise<boolean>——不要用 async 回调（返回值不是 awaitable）
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await userStore.login(form)
    ElMessage.success('登录成功')
    router.replace(sanitizeRedirect(route.query.redirect as string | undefined))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    class="relative h-screen w-full overflow-hidden flex items-center justify-center bg-[linear-gradient(135deg,var(--el-color-primary-light-3),var(--el-color-primary-dark-2))]"
  >
    <div
      class="absolute -top-24 -left-24 h-96 w-96 rounded-full bg-white/40 opacity-30 blur-3xl dark:bg-white/10"
    ></div>
    <div
      class="absolute -right-32 -bottom-32 h-[28rem] w-[28rem] rounded-full bg-white/40 opacity-30 blur-3xl dark:bg-white/10"
    ></div>

    <div
      class="relative w-96 max-w-[90vw] rounded-2xl border border-white/60 bg-white/80 p-8 shadow-2xl backdrop-blur-xl dark:border-white/10 dark:bg-[#1d1d1f]/80"
    >
      <div class="mb-8 flex flex-col items-center gap-1">
        <img src="/youzi-logo.svg" alt="logo" class="mb-1 h-12 w-12" />
        <h1 class="text-2xl font-bold text-gray-800 dark:text-gray-100">{{ APP_TITLE }}</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">管理系统</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="onSubmit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="'User'" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            show-password
            :prefix-icon="'Lock'"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="onSubmit">
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <p class="mt-4 text-center text-xs text-gray-500 dark:text-gray-400">
        默认账号 admin，密码见 backend/.env 的 INITIAL_ADMIN_PASSWORD
      </p>
    </div>
  </div>
</template>
