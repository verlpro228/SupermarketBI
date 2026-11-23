<script setup lang="ts">
import { ref, watch } from 'vue'

import { listStockRecords } from '@/api/stock'
import type { StockInfo, StockRecord } from '@/types'
import { formatDaysLeft, formatDateTime, formatMoney, formatQty } from '@/utils/format'

const visible = defineModel<boolean>({ required: true })

const props = defineProps<{
  product?: StockInfo | null
}>()

const loading = ref(false)
const rows = ref<StockRecord[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

async function fetchRecords() {
  if (!props.product) return
  loading.value = true
  try {
    const { data } = await listStockRecords(props.product.product_id, {
      page: page.value,
      page_size: pageSize.value,
    })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

watch(visible, (opened) => {
  if (!opened) return
  page.value = 1
  rows.value = []
  total.value = 0
  fetchRecords()
})
</script>

<template>
  <el-drawer
    v-model="visible"
    :title="`出入库流水 - ${props.product?.name ?? ''}`"
    size="72%"
    destroy-on-close
  >
    <div class="summary">
      <el-descriptions :column="4" border size="small">
        <el-descriptions-item label="条码">{{ props.product?.barcode || '-' }}</el-descriptions-item>
        <el-descriptions-item label="当前库存">
          {{ formatQty(props.product?.total_qty) }}
        </el-descriptions-item>
        <el-descriptions-item label="安全库存">
          {{ formatQty(props.product?.safe_stock) }}
        </el-descriptions-item>
        <el-descriptions-item label="最近到期日">
          {{ props.product?.nearest_expiry || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column label="类型" width="90" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.record_type === 'inbound'" type="success" size="small">入库</el-tag>
          <el-tag v-else-if="row.outbound_type === 'loss'" type="danger" size="small">报损</el-tag>
          <el-tag v-else type="warning" size="small">销售</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="order_no" label="单号" width="150" />
      <el-table-column prop="batch_no" label="批次号" width="150" show-overflow-tooltip />
      <el-table-column label="数量" width="90" align="right">
        <template #default="{ row }">{{ formatQty(row.quantity) }}</template>
      </el-table-column>
      <el-table-column label="金额" width="110" align="right">
        <template #default="{ row }">{{ formatMoney(row.amount) }}</template>
      </el-table-column>
      <el-table-column prop="production_date" label="生产日期" width="110" />
      <el-table-column prop="expiry_date" label="到期日" width="110" />
      <el-table-column label="剩余天数" width="110" align="center">
        <template #default="{ row }">
          <span :class="{ expired: row.days_left !== null && row.days_left < 0 }">
            {{ formatDaysLeft(row.days_left) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="供应商 / 原因" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">{{ row.supplier || row.reason || '-' }}</template>
      </el-table-column>
      <el-table-column prop="operator_name" label="操作人" width="100" />
      <el-table-column label="时间" width="170">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
    </el-table>

    <div class="pagination-bar">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="fetchRecords"
        @size-change="fetchRecords"
      />
    </div>
  </el-drawer>
</template>

<style scoped>
.summary {
  margin-bottom: 16px;
}

.expired {
  color: #f56c6c;
  font-weight: 600;
}
</style>
