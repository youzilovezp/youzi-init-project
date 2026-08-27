<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import * as userApi from '@/api/user'
import * as roleApi from '@/api/role'
import type { UserInfo } from '@/api/types'
import type { Role } from '@/api/role'
import { useUserStore } from '@/stores/user'
import { formatTime } from '@/utils/format'

const userStore = useUserStore()
const loading = ref(false)
const tableData = ref<UserInfo[]>([])
const total = ref(0)
const roles = ref<Role[]>([])

const query = reactive({
  page: 1,
  page_size: 20,
  username: '',
  is_active: undefined as boolean | undefined,
})

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const formRef = ref<FormInstance>()

const formRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
}
const form = reactive({
  id: 0,
  username: '',
  nickname: '',
  email: '',
  phone: '',
  password: '',
  role_id: undefined as number | undefined,
  is_active: true,
})

async function fetchData() {
  loading.value = true
  try {
    const data = await userApi.listUsers(query)
    tableData.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function fetchRoles() {
  roles.value = await roleApi.listRoles()
}

function openCreate() {
  dialogMode.value = 'create'
  Object.assign(form, {
    id: 0,
    username: '',
    nickname: '',
    email: '',
    phone: '',
    password: '',
    role_id: undefined,
    is_active: true,
  })
  dialogVisible.value = true
}

function openEdit(row: UserInfo) {
  dialogMode.value = 'edit'
  // 显式 pick 字段，避免 spread 把 is_superuser/avatar/created_at 也注入 form
  // （那些字段不可编辑，注入会导致表单提交时多带参数）
  Object.assign(form, {
    id: row.id,
    username: row.username,
    nickname: row.nickname ?? '',
    email: row.email ?? '',
    phone: row.phone ?? '',
    role_id: row.role_id,
    is_active: row.is_active,
    password: '',
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  // Element Plus validate() 返回 Promise<boolean>——用 await + 非 async 回调
  // 之前 await formRef.value.validate(async (valid) => {...}) 是错的：
  // validate 回调签名是 sync (valid: boolean) => void，async 函数返回 void 不会
  // 变成 awaitable，会让 fetchData 在 valid=false 时也执行，请求仍发出
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (dialogMode.value === 'create') {
    await userApi.createUser({
      username: form.username,
      password: form.password,
      nickname: form.nickname,
      email: form.email,
      phone: form.phone,
      role_id: form.role_id,
      is_active: form.is_active,
    })
    ElMessage.success('创建成功')
  } else {
    await userApi.updateUser(form.id, {
      nickname: form.nickname,
      email: form.email,
      phone: form.phone,
      role_id: form.role_id,
      is_active: form.is_active,
    })
    ElMessage.success('更新成功')
  }
  dialogVisible.value = false
  fetchData()
}

async function handleDelete(row: UserInfo) {
  // 前端二次校验：不能删除自己（防误操作）
  if (row.id === userStore.userInfo?.id) {
    ElMessage.error('不能删除自己')
    return
  }
  // 前端提示：删除 superuser 是高危操作（后端也会校验最后一个 superuser）
  const warning = row.is_superuser
    ? `确定要删除超级管理员「${row.username}」吗？删除后系统将无法恢复。`
    : `确定删除用户「${row.username}」吗？`
  const ok = await ElMessageBox.confirm(warning, '⚠️ 危险操作', { type: 'warning' }).catch(() => false)
  if (ok === false) return
  await userApi.deleteUser(row.id)
  ElMessage.success('已删除')
  fetchData()
}

onMounted(() => {
  fetchData()
  fetchRoles()
})
</script>

<template>
  <div class="page">
    <!-- 搜索栏 -->
    <el-form class="mb-4" :inline="true" :model="query">
      <el-form-item label="用户名">
        <el-input v-model="query.username" clearable placeholder="模糊搜索" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="query.is_active" clearable placeholder="全部" style="width: 140px">
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="() => { query.page = 1; fetchData() }">查询</el-button>
        <el-button @click="() => { query.username = ''; query.is_active = undefined; fetchData() }">重置</el-button>
        <el-button type="success" @click="openCreate">新增用户</el-button>
      </el-form-item>
    </el-form>

    <!-- 表格 -->
    <div class="rounded-lg overflow-hidden border border-border">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="nickname" label="昵称" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="role_name" label="角色" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="openEdit(scope.row as UserInfo)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(scope.row as UserInfo)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="flex justify-end mt-4">
      <el-pagination
        :current-page="query.page"
        :page-size="query.page_size"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        :page-sizes="[10, 20, 50, 100]"
        @current-change="(p: number) => { query.page = p; fetchData() }"
        @size-change="(s: number) => { query.page_size = s; query.page = 1; fetchData() }"
      />
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增用户' : '编辑用户'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item v-if="dialogMode === 'create'" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_id" placeholder="请选择" style="width: 100%">
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>
