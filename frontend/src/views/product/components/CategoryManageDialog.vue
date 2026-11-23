<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import {
  createCategory,
  listCategories,
  updateCategory,
  updateCategoryStatus,
} from '@/api/category'
import type { CategoryInfo } from '@/types'

const visible = defineModel<boolean>({ required: true })
const emit = defineEmits<{ change: [] }>()

const loading = ref(false)
const rows = ref<CategoryInfo[]>([])
const adding = ref(false)
const newForm = reactive({ name: '', sort_order: 0 })

const editingId = ref<number | null>(null)
const editingName = ref('')
const editingSort = ref(0)

async function fetchList() {
  loading.value = true
  try {
    const { data } = await listCategories()
    rows.value = data
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  const name = newForm.name.trim()
  if (!name) {
    ElMessage.warning('请输入分类名称')
    return
  }
  adding.value = true
  try {
    await createCategory({ name, sort_order: newForm.sort_order })
    ElMessage.success('新增成功')
    newForm.name = ''
    newForm.sort_order = 0
    await fetchList()
    emit('change')
  } finally {
    adding.value = false
  }
}

function startEdit(row: CategoryInfo) {
  editingId.value = row.id
  editingName.value = row.name
  editingSort.value = row.sort_order
}

function cancelEdit() {
  editingId.value = null
}

async function saveEdit(row: CategoryInfo) {
  const name = editingName.value.trim()
  if (!name) {
    ElMessage.warning('名称不能为空')
    return
  }
  await updateCategory(row.id, { name, sort_order: editingSort.value })
  ElMessage.success('保存成功')
  editingId.value = null
  await fetchList()
  emit('change')
}

async function toggleStatus(row: CategoryInfo) {
  const next = row.status === 1 ? 0 : 1
  try {
    await ElMessageBox.confirm(
      `确定要${next === 1 ? '启用' : '停用'}分类「${row.name}」吗？`,
      '提示',
      { type: 'warning' },
    )
  } catch {
    return
  }

  await updateCategoryStatus(row.id, next)
  ElMessage.success('状态已更新')
  await fetchList()
  emit('change')
}

onMounted(fetchList)
</script>

<template>
  <el-dialog v-model="visible" title="分类管理" width="620px">
    <div class="add-bar">
      <el-input
        v-model="newForm.name"
        placeholder="新分类名称"
        maxlength="50"
        style="width: 220px"
        @keyup.enter="handleAdd"
      />
      <el-input-number v-model="newForm.sort_order" :min="0" :max="9999" controls-position="right" />
      <el-button type="primary" :loading="adding" @click="handleAdd">新增</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" border size="small" max-height="380">
      <el-table-column label="分类名称" min-width="180">
        <template #default="{ row }">
          <el-input
            v-if="editingId === row.id"
            v-model="editingName"
            size="small"
            maxlength="50"
          />
          <span v-else>{{ row.name }}</span>
        </template>
      </el-table-column>

      <el-table-column label="排序" width="120" align="center">
        <template #default="{ row }">
          <el-input-number
            v-if="editingId === row.id"
            v-model="editingSort"
            size="small"
            :min="0"
            :max="9999"
            controls-position="right"
            style="width: 90px"
          />
          <span v-else>{{ row.sort_order }}</span>
        </template>
      </el-table-column>

      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
            {{ row.status === 1 ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="150" align="center">
        <template #default="{ row }">
          <template v-if="editingId === row.id">
            <el-button link type="primary" @click="saveEdit(row)">保存</el-button>
            <el-button link @click="cancelEdit">取消</el-button>
          </template>
          <template v-else>
            <el-button link type="primary" @click="startEdit(row)">编辑</el-button>
            <el-button link :type="row.status === 1 ? 'danger' : 'success'" @click="toggleStatus(row)">
              {{ row.status === 1 ? '停用' : '启用' }}
            </el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.add-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}
</style>
