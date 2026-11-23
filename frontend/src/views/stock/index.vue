<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { listCategories } from '@/api/category'
import { downloadExport } from '@/api/export'
import { listStock } from '@/api/stock'
import { useUserStore } from '@/stores/user'
import type { CategoryInfo, StockInfo, StockQuery } from '@/types'
import { formatDaysLeft, formatMoney, formatQty } from '@/utils/format'

import StockAdjustDialog from './components/StockAdjustDialog.vue'
import StockRecordDrawer from './components/StockRecordDrawer.vue'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin)

const loading = ref(false)
const rows = ref<StockInfo[]>([])
const total = ref(0)
const categories = ref<CategoryInfo[]>([])

const query = reactive<StockQuery>({
  page: 1,
  page_size: 20,
  keyword: '',
  category_id: undefined,
  status: undefined,
})

const drawerVisible = ref(false)
const adjustVisible = ref(false)
const currentProduct = ref<StockInfo | null>(null)

async function fetchList() {
  loading.value = true
  try {
    const { data } = await listStock({ ...query, keyword: query.keyword || undefined })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function fetchCategories() {
  const { data } = await listCategories()
  categories.value = data
}

function handleSearch() {
  query.page = 1
  fetchList()
}

function handleReset() {
  query.keyword = ''
  query.category_id = undefined
  query.status = undefined
  query.page = 1
  fetchList()
}

function openRecords(row: StockInfo) {
  currentProduct.value = row
  drawerVisible.value = true
}

function openAdjust(row: StockInfo) {
  currentProduct.value = row
  adjustVisible.value = true
}

const exporting = ref(false)

async function handleExport() {
  exporting.value = true
  try {
    await downloadExport(
      'stock',
      {
        keyword: query.keyword || undefined,
        category_id: query.category_id,
        status: query.status,
      },
      '库存列表.xlsx',
    )
    ElMessage.success('导出成功')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  fetchCategories()
  fetchList()
})
</script>

<template>
  <div class="page-card">
    <div class="table-toolbar">
      <el-form :inline="true" :model="query" @submit.prevent>
        <el-form-item label="关键词">
          <el-input
            v-model="query.keyword"
            placeholder="名称 / 条码"
            clearable
            style="width: 190px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="query.category_id" placeholder="全部" clearable style="width: 140px">
            <el-option
              v-for="item in categories"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="正常" :value="1" />
            <el-option label="已停用" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-button :loading="exporting" @click="handleExport">导出 Excel</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="name" label="商品" min-width="170" show-overflow-tooltip />
      <el-table-column prop="barcode" label="条码" width="140" show-overflow-tooltip />
      <el-table-column label="分类" width="110">
        <template #default="{ row }">{{ row.category_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="当前库存" width="120" align="right">
        <template #default="{ row }">
          <span :class="{ 'low-stock': row.is_low_stock }">
            {{ formatQty(row.total_qty) }}
          </span>
          <el-tag v-if="row.is_low_stock" type="danger" size="small" effect="plain" class="low-tag">
            低
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="安全库存" width="100" align="right">
        <template #default="{ row }">{{ formatQty(row.safe_stock) }}</template>
      </el-table-column>
      <el-table-column v-if="isAdmin" label="库存货值" width="120" align="right">
        <template #default="{ row }">{{ formatMoney(row.stock_value) }}</template>
      </el-table-column>
      <el-table-column label="最近到期日" width="110" align="center">
        <template #default="{ row }">{{ row.nearest_expiry || '-' }}</template>
      </el-table-column>
      <el-table-column label="剩余天数" width="110" align="center">
        <template #default="{ row }">
          <span :class="{ expired: row.days_left !== null && row.days_left < 0 }">
            {{ formatDaysLeft(row.days_left) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.product_status === 1 ? 'success' : 'info'" size="small">
            {{ row.product_status === 1 ? '正常' : '已停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" :width="isAdmin ? 160 : 100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openRecords(row)">流水</el-button>
          <el-button v-if="isAdmin" link type="warning" @click="openAdjust(row)">调整库存</el-button>
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

    <StockRecordDrawer v-model="drawerVisible" :product="currentProduct" />
    <StockAdjustDialog
      v-model="adjustVisible"
      :product="currentProduct"
      @success="fetchList"
    />
  </div>
</template>

<style scoped>
.low-stock {
  color: #f56c6c;
  font-weight: 600;
}

.low-tag {
  margin-left: 6px;
}

.expired {
  color: #f56c6c;
  font-weight: 600;
}
</style>
