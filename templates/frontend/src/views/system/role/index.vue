<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import * as roleApi from '@/api/role'
import type { Role } from '@/api/role'

const loading = ref(false)
const tableData = ref<Role[]>([])

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const formRef = ref<FormInstance>()
const formRules: FormRules = {
  name: [{ required: true, message: '请输入角色名', trigger: 'blur' }],
  code: [{ required: true, message: '请输入角色编码', trigger: 'blur' }],
}
const form = reactive({
  id: 0,
  name: '',
  code: '',
  remark: '',
})

async function fetchData() {
  loading.value = true
  try {
    tableData.value = await roleApi.listRoles()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialogMode.value = 'create'
  Object.assign(form, { id: 0, name: '', code: '', remark: '' })
  dialogVisible.value = true
}

function openEdit(row: Role) {
  dialogMode.value = 'edit'
  // 显式 pick 字段，避免 spread 把 created_at 也注入 form
  Object.assign(form, {
    id: row.id,
    name: row.name,
    code: row.code,
    remark: row.remark ?? '',
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
    await roleApi.createRole({ name: form.name, code: form.code, remark: form.remark })
    ElMessage.success('创建成功')
  } else {
    await roleApi.updateRole(form.id, { name: form.name, code: form.code, remark: form.remark })
    ElMessage.success('更新成功')
  }
  dialogVisible.value = false
  fetchData()
}

async function handleDelete(row: Role) {
  await ElMessageBox.confirm(`确定删除角色「${row.name}」吗？`, '提示', { type: 'warning' })
  await roleApi.deleteRole(row.id)
  ElMessage.success('已删除')
  fetchData()
}

onMounted(fetchData)
</script>

<template>
  <div class="page">
    <el-card>
      <div style="margin-bottom: 16px">
        <el-button type="success" @click="openCreate">新增角色</el-button>
      </div>

      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="角色名" />
        <el-table-column prop="code" label="角色编码" />
        <el-table-column prop="remark" label="备注" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="openEdit(scope.row as Role)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(scope.row as Role)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增角色' : '编辑角色'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px">
        <el-form-item label="角色名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="角色编码" prop="code">
          <el-input v-model="form.code" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>
