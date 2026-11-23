<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { listInspections, runInspection } from '@/api/inspection'
import type { InspectionRecord } from '@/types'
import { formatDateTime } from '@/utils/format'

import InspectionDetailDrawer from './components/InspectionDetailDrawer.vue'

const loading = ref(false)
const running = ref(false)
const rows = ref<InspectionRecord[]>([])
const total = ref(0)

const query = reactive({ page: 1, page_size: 10 })

const drawerVisible = ref(false)
const activeRecordId = ref<number | null>(null)

async function fetchList() {
  loading.value = true
  try {
    const { data } = await listInspections({ ...query })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function handleRun() {
  running.value = true
  try {
    const { data } = await runInspection()
    ElMessage.success(`巡检完成，命中 ${data.hit_count} 条问题`)
    query.page = 1
    await fetchList()
    activeRecordId.value = data.id
    drawerVisible.value = true
  } finally {
    running.value = false
  }
}

function openDetail(row: InspectionRecord) {
  activeRecordId.value = row.id
  drawerVisible.value = true
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="table-toolbar">
      <div class="title-block">
        <div class="card-title">库存巡检</div>
        <div class="hint">
          巡检会扫描当前库存，命中「低库存」与「临期」两类问题，并保存当次快照
        </div>
      </div>
      <el-button type="primary" :loading="running" @click="handleRun">开始巡检</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" stripe class="inspection-table">
      <el-table-column label="巡检时间" min-width="180">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column prop="inspector_name" label="执行人" min-width="120">
        <template #default="{ row }">{{ row.inspector_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="命中条数" min-width="110" align="right">
        <template #default="{ row }">
          <span class="num-strong">{{ row.hit_count }}</span>
        </template>
      </el-table-column>
      <el-table-column label="低库存" min-width="100" align="right">
        <template #default="{ row }">
          <span class="num">{{ row.low_stock_count }}</span>
        </template>
      </el-table-column>
      <el-table-column label="临期" min-width="100" align="right">
        <template #default="{ row }">
          <span class="num">{{ row.near_expiry_count }}</span>
        </template>
      </el-table-column>
      <el-table-column label="待处理" min-width="110" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.pending_count > 0" type="warning" size="small" effect="light">
            {{ row.pending_count }} 条
          </el-tag>
          <el-tag v-else type="success" size="small" effect="light">已清空</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="120" align="center">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">查看详情</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无巡检记录，点击右上角「开始巡检」" :image-size="80" />
      </template>
    </el-table>

    <div class="pagination-bar">
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="fetchList"
        @size-change="fetchList"
      />
    </div>

    <InspectionDetailDrawer
      v-model="drawerVisible"
      :record-id="activeRecordId"
      @changed="fetchList"
    />
  </div>
</template>

<style scoped>
.title-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1b2a41;
}

.hint {
  color: #8b98ac;
  font-size: 13px;
}

.num {
  color: #56647d;
  font-variant-numeric: tabular-nums;
}

.num-strong {
  color: #1b2a41;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
</style>
