<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'

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
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
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
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.login(form)
      ElMessage.success('登录成功')
      // 修复：之前直接 router.push(route.query.redirect) 是 open redirect 漏洞。
      // 攻击者构造 /login?redirect=//evil.com 可把用户重定向到外部域名。
      // 现在只接受以单个 / 开头（不是 // 协议相对、不是 javascript: 等）
      const raw = route.query.redirect as string | undefined
      const redirect =
        raw && raw.startsWith('/') && !raw.startsWith('//') ? raw : '/dashboard'
      router.replace(redirect)
    } finally {
      loading.value = false
    }
  })
}
</script>

<template>
  <div class="login-page">
    <div class="login-box">
      <h1 class="title">Youzi Admin</h1>
      <p class="subtitle">管理系统</p>

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

      <p class="tips">首次登录请使用后端启动时控制台打印的随机密码（详见后端说明）</p>
    </div>
  </div>
</template>

<style scoped lang="scss">
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1890ff 0%, #003a8c 100%);
}

.login-box {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.title {
  font-size: 24px;
  font-weight: bold;
  text-align: center;
  margin: 0 0 8px;
  color: #1890ff;
}

.subtitle {
  text-align: center;
  color: #999;
  margin: 0 0 32px;
}

.tips {
  text-align: center;
  color: #999;
  font-size: 12px;
  margin-top: 16px;
}
</style>
