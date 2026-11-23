<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { listUsers, updateUserStatus } from '@/api/user'
import { ROLE_LABEL } from '@/constants'
import { useUserStore } from '@/stores/user'
import type { UserInfo, UserListQuery } from '@/types'
import { formatDateTime } from '@/utils/format'

import ResetPwdDialog from './components/ResetPwdDialog.vue'
import UserFormDialog from './components/UserFormDialog.vue'

const userStore = useUserStore()

const loading = ref(false)
const rows = ref<UserInfo[]>([])
const total = ref(0)

const query = reactive<UserListQuery>({
  page: 1,
  page_size: 20,
  keyword: '',
  role: undefined,
  status: undefined,
})

const formVisible = ref(false)
const editingUser = ref<UserInfo | null>(null)
const pwdVisible = ref(false)
const pwdUser = ref<UserInfo | null>(null)

async function fetchList() {
  loading.value = true
  try {
    const { data } = await listUsers({ ...query, keyword: query.keyword || undefined })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  query.page = 1
  fetchList()
}

function handleReset() {
  query.keyword = ''
  query.role = undefined
  query.status = undefined
  query.page = 1
  fetchList()
}

function handleCreate() {
  editingUser.value = null
  formVisible.value = true
}

function handleEdit(row: UserInfo) {
  editingUser.value = row
  formVisible.value = true
}

function handleResetPwd(row: UserInfo) {
  pwdUser.value = row
  pwdVisible.value = true
}

async function handleToggleStatus(row: UserInfo, enabled: boolean) {
  const action = enabled ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm(`确定要${action}账号「${row.username}」吗？`, '提示', {
      type: 'warning',
    })
  } catch {
    return
  }

  try {
    await updateUserStatus(row.id, enabled ? 1 : 0)
    ElMessage.success(`已${action}`)
  } finally {
    fetchList()
  }
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="table-toolbar">
      <el-form :inline="true" :model="query" @submit.prevent>
        <el-form-item label="关键词">
          <el-input
            v-model="query.keyword"
            placeholder="账号 / 姓名"
            clearable
            style="width: 180px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="query.role" placeholder="全部" clearable style="width: 130px">
            <el-option label="管理员" value="admin" />
            <el-option label="库管员" value="keeper" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-button type="primary" @click="handleCreate">新增用户</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="username" label="账号" min-width="130" />
      <el-table-column label="姓名" min-width="110">
        <template #default="{ row }">{{ row.real_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small" effect="plain">
            {{ ROLE_LABEL[row.role] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-switch
            :model-value="row.status === 1"
            :disabled="row.id === userStore.user?.id"
            @change="handleToggleStatus(row, Boolean($event))"
          />
        </template>
      </el-table-column>
      <el-table-column label="最后登录" width="170">
        <template #default="{ row }">{{ formatDateTime(row.last_login_at) }}</template>
      </el-table-column>
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="warning" @click="handleResetPwd(row)">重置密码</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-bar">
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="fetchList"
        @size-change="handleSearch"
      />
    </div>

    <UserFormDialog
      v-model="formVisible"
      :user="editingUser"
      @success="fetchList"
    />

    <ResetPwdDialog v-model="pwdVisible" :user="pwdUser" @success="fetchList" />
  </div>
</template>
