<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { ref, watch } from 'vue'

import { getInspection, updateInspectionItems } from '@/api/inspection'
import { INSPECTION_STATUS_LABEL } from '@/constants'
import type { InspectionDetail, InspectionItem } from '@/types'
import { formatDateTime, formatDaysLeft, formatQty } from '@/utils/format'

const visible = defineModel<boolean>({ required: true })

const props = defineProps<{
  recordId: number | null
}>()

const emit = defineEmits<{ changed: [] }>()

const loading = ref(false)
const detail = ref<InspectionDetail | null>(null)
const selected = ref<InspectionItem[]>([])
const submitting = ref(false)

async function fetchDetail() {
  if (!props.recordId) return
  loading.value = true
  try {
    const { data } = await getInspection(props.recordId)
    detail.value = data
  } finally {
    loading.value = false
  }
}

watch(visible, (opened) => {
  if (!opened) return
  detail.value = null
  selected.value = []
  fetchDetail()
})

function handleSelectionChange(selection: InspectionItem[]) {
  selected.value = selection
}

async function mark(status: 'handled' | 'ignored', ids: number[]) {
  if (ids.length === 0) {
    ElMessage.warning('请先选择需要处理的明细')
    return
  }
  submitting.value = true
  try {
    await updateInspectionItems(ids, status)
    ElMessage.success(status === 'handled' ? '已标记为已处理' : '已标记为已忽略')
    await fetchDetail()
    emit('changed')
  } finally {
    submitting.value = false
  }
}

function statusTagType(status: string) {
  if (status === 'handled') return 'success'
  if (status === 'ignored') return 'info'
  return 'warning'
}
</script>

<template>
  <el-drawer v-model="visible" title="巡检详情" size="76%" destroy-on-close>
    <div v-loading="loading">
      <el-descriptions v-if="detail" :column="5" border size="small" style="margin-bottom: 16px">
        <el-descriptions-item label="巡检时间">
          {{ formatDateTime(detail.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="执行人">{{ detail.inspector_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="命中条数">{{ detail.hit_count }}</el-descriptions-item>
        <el-descriptions-item label="低库存 / 临期">
          {{ detail.low_stock_count }} / {{ detail.near_expiry_count }}
        </el-descriptions-item>
        <el-descriptions-item label="待处理">{{ detail.pending_count }}</el-descriptions-item>
      </el-descriptions>

      <div class="toolbar">
        <span class="selected-hint">已选 {{ selected.length }} 条</span>
        <div>
          <el-button
            type="success"
            :loading="submitting"
            :disabled="selected.length === 0"
            @click="mark('handled', selected.map((item) => item.id))"
          >
            标记已处理
          </el-button>
          <el-button
            :loading="submitting"
            :disabled="selected.length === 0"
            @click="mark('ignored', selected.map((item) => item.id))"
          >
            标记已忽略
          </el-button>
        </div>
      </div>

      <el-table
        :data="detail?.items ?? []"
        border
        stripe
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column label="问题类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.problem_type === 'low_stock' ? 'danger' : 'warning'" size="small">
              {{ row.problem_type === 'low_stock' ? '低库存' : '临期' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="商品" min-width="160" show-overflow-tooltip />
        <el-table-column prop="barcode" label="条码" width="130" show-overflow-tooltip />
        <el-table-column label="批次" width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.batch_no || '-' }}</template>
        </el-table-column>
        <el-table-column label="缺口数量" width="110" align="right">
          <template #default="{ row }">
            {{ row.gap_qty !== null ? formatQty(row.gap_qty) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="剩余天数" width="110" align="center">
          <template #default="{ row }">
            <span v-if="row.days_left !== null" :class="{ expired: row.days_left < 0 }">
              {{ formatDaysLeft(row.days_left) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ INSPECTION_STATUS_LABEL[row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="处理时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.handled_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="success"
              :disabled="row.status === 'handled'"
              @click="mark('handled', [row.id])"
            >
              已处理
            </el-button>
            <el-button
              link
              :disabled="row.status === 'ignored'"
              @click="mark('ignored', [row.id])"
            >
              忽略
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </el-drawer>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.selected-hint {
  color: #909399;
  font-size: 13px;
}

.expired {
  color: #f56c6c;
  font-weight: 600;
}
</style>
