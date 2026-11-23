<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { listCategories } from '@/api/category'
import { downloadExport } from '@/api/export'
import {
  listExpiry,
  listExpiryActions,
  markExpiryPromo,
} from '@/api/expiry'
import { EXPIRY_LEVEL_LABEL } from '@/constants'
import { useUserStore } from '@/stores/user'
import type {
  CategoryInfo,
  ExpiryActionLog,
  ExpiryActionQuery,
  ExpiryBatch,
  ExpiryQuery,
  ExpiryThresholds,
} from '@/types'
import { formatDateTime, formatDaysLeft, formatMoney, formatQty } from '@/utils/format'

import LossDialog from './components/LossDialog.vue'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin)

const activeTab = ref<'pending' | 'records'>('pending')

const rows = ref<ExpiryBatch[]>([])
const total = ref(0)
const loading = ref(false)
const categories = ref<CategoryInfo[]>([])
const thresholds = ref<ExpiryThresholds>({ urgent_days: 7, warning_days: 30 })
const selectedRows = ref<ExpiryBatch[]>([])

const query = reactive<ExpiryQuery>({
  page: 1,
  page_size: 20,
  level: undefined,
  category_id: undefined,
  keyword: '',
})

const lossVisible = ref(false)
const lossBatches = ref<ExpiryBatch[]>([])

async function fetchExpiry() {
  loading.value = true
  try {
    const { data } = await listExpiry({ ...query, keyword: query.keyword || undefined })
    rows.value = data.items
    total.value = data.total
    thresholds.value = data.thresholds
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
  fetchExpiry()
}

function handleReset() {
  query.level = undefined
  query.category_id = undefined
  query.keyword = ''
  query.page = 1
  fetchExpiry()
}

function handleSelectionChange(selection: ExpiryBatch[]) {
  selectedRows.value = selection
}

function openSingleLoss(row: ExpiryBatch) {
  lossBatches.value = [row]
  lossVisible.value = true
}

function openBatchLoss() {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先勾选需要报损的批次')
    return
  }
  lossBatches.value = [...selectedRows.value]
  lossVisible.value = true
}

async function handlePromo(row: ExpiryBatch) {
  try {
    await ElMessageBox.confirm(
      `确定为批次「${row.batch_no}」标记促销吗？标记后该批次不再出现在待处理清单。`,
      '标记促销',
      { type: 'warning' },
    )
  } catch {
    return
  }

  await markExpiryPromo(row.batch_id)
  ElMessage.success('已标记为促销')
  fetchExpiry()
  if (activeTab.value === 'records') fetchActions()
}

const actions = ref<ExpiryActionLog[]>([])
const actionTotal = ref(0)
const actionLoading = ref(false)
const actionQuery = reactive<ExpiryActionQuery>({
  page: 1,
  page_size: 10,
  keyword: '',
  action: undefined,
})

async function fetchActions() {
  actionLoading.value = true
  try {
    const { data } = await listExpiryActions({
      ...actionQuery,
      keyword: actionQuery.keyword || undefined,
    })
    actions.value = data.items
    actionTotal.value = data.total
  } finally {
    actionLoading.value = false
  }
}

function handleActionSearch() {
  actionQuery.page = 1
  fetchActions()
}

function handleTabChange(name: string | number) {
  if (name === 'records') {
    fetchActions()
  } else {
    fetchExpiry()
  }
}

function levelTagType(level: string) {
  if (level === 'expired') return 'danger'
  if (level === 'urgent') return 'warning'
  return 'info'
}

function handleLossSuccess() {
  fetchExpiry()
  if (activeTab.value === 'records') fetchActions()
}

const exporting = ref(false)

async function handleExport() {
  exporting.value = true
  try {
    await downloadExport(
      'expiry',
      {
        level: query.level,
        category_id: query.category_id,
        keyword: query.keyword || undefined,
      },
      '临期清单.xlsx',
    )
    ElMessage.success('导出成功')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  fetchCategories()
  fetchExpiry()
})
</script>

<template>
  <div class="page-card">
    <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
      <template #title>
        分档规则：剩余天数 &lt; 0 为已过期；0 ~ {{ thresholds.urgent_days }} 天为紧急；{{
          thresholds.urgent_days
        }}
        ~ {{ thresholds.warning_days }} 天为预警。阈值由系统配置项控制。
      </template>
    </el-alert>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="待处理" name="pending">
        <div class="table-toolbar">
          <el-form :inline="true" :model="query" @submit.prevent>
            <el-form-item label="分档">
              <el-select v-model="query.level" placeholder="全部" clearable style="width: 130px">
                <el-option label="已过期" value="expired" />
                <el-option label="紧急" value="urgent" />
                <el-option label="预警" value="warning" />
              </el-select>
            </el-form-item>
            <el-form-item label="分类">
              <el-select
                v-model="query.category_id"
                placeholder="全部"
                clearable
                style="width: 140px"
              >
                <el-option
                  v-for="item in categories"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="关键词">
              <el-input
                v-model="query.keyword"
                placeholder="名称 / 条码"
                clearable
                style="width: 170px"
                @keyup.enter="handleSearch"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSearch">查询</el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-form-item>
          </el-form>

          <div class="toolbar-actions">
            <el-button :loading="exporting" @click="handleExport">导出 Excel</el-button>
            <el-button
              type="danger"
              :disabled="selectedRows.length === 0"
              @click="openBatchLoss"
            >
              批量报损（{{ selectedRows.length }}）
            </el-button>
          </div>
        </div>

        <el-table
          v-loading="loading"
          :data="rows"
          border
          stripe
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="48" />
          <el-table-column prop="product_name" label="商品" min-width="160" show-overflow-tooltip />
          <el-table-column prop="barcode" label="条码" width="130" show-overflow-tooltip />
          <el-table-column prop="batch_no" label="批次号" width="150" show-overflow-tooltip />
          <el-table-column prop="production_date" label="生产日期" width="110" />
          <el-table-column prop="expiry_date" label="到期日" width="110" />
          <el-table-column label="剩余天数" width="110" align="center">
            <template #default="{ row }">
              <span :class="{ expired: row.days_left < 0 }">
                {{ formatDaysLeft(row.days_left) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="90" align="right">
            <template #default="{ row }">{{ formatQty(row.qty_remaining) }}</template>
          </el-table-column>
          <el-table-column v-if="isAdmin" label="货值" width="110" align="right">
            <template #default="{ row }">{{ formatMoney(row.stock_value) }}</template>
          </el-table-column>
          <el-table-column label="分档" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="levelTagType(row.level)" size="small">
                {{ EXPIRY_LEVEL_LABEL[row.level] }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button link type="danger" @click="openSingleLoss(row)">报损</el-button>
              <el-button link type="warning" @click="handlePromo(row)">标记促销</el-button>
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
            @current-change="fetchExpiry"
            @size-change="handleSearch"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="处理记录" name="records">
        <div class="table-toolbar">
          <el-form :inline="true" :model="actionQuery" @submit.prevent>
            <el-form-item label="处理方式">
              <el-select
                v-model="actionQuery.action"
                placeholder="全部"
                clearable
                style="width: 130px"
              >
                <el-option label="报损" value="loss" />
                <el-option label="标记促销" value="promo" />
              </el-select>
            </el-form-item>
            <el-form-item label="关键词">
              <el-input
                v-model="actionQuery.keyword"
                placeholder="名称 / 条码"
                clearable
                style="width: 170px"
                @keyup.enter="handleActionSearch"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleActionSearch">查询</el-button>
            </el-form-item>
          </el-form>
        </div>

        <el-table v-loading="actionLoading" :data="actions" border stripe>
          <el-table-column prop="product_name" label="商品" min-width="160" show-overflow-tooltip />
          <el-table-column prop="batch_no" label="批次号" width="150" show-overflow-tooltip />
          <el-table-column label="处理方式" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="row.action === 'loss' ? 'danger' : 'warning'" size="small">
                {{ row.action === 'loss' ? '报损' : '标记促销' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="处理数量" width="110" align="right">
            <template #default="{ row }">{{ formatQty(row.quantity) }}</template>
          </el-table-column>
          <el-table-column prop="order_no" label="关联出库单" width="150">
            <template #default="{ row }">{{ row.order_no || '-' }}</template>
          </el-table-column>
          <el-table-column prop="operator_name" label="处理人" width="110" />
          <el-table-column label="处理时间" width="170">
            <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>

        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="actionQuery.page"
            v-model:page-size="actionQuery.page_size"
            :total="actionTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="fetchActions"
            @size-change="handleActionSearch"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <LossDialog
      v-model="lossVisible"
      :batches="lossBatches"
      @success="handleLossSuccess"
    />
  </div>
</template>

<style scoped>
.expired {
  color: #f56c6c;
  font-weight: 600;
}

.toolbar-actions {
  display: flex;
  gap: 10px;
}
</style>
