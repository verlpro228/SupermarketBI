<script setup lang="ts">
import type { EChartsOption } from 'echarts'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { downloadExport } from '@/api/export'
import { createOutbound, listOutbounds } from '@/api/outbound'
import { listProductOptions } from '@/api/product'
import { getOutboundAnalysis } from '@/api/stats'
import BaseChart from '@/components/common/BaseChart.vue'
import { OUTBOUND_TYPE_LABEL } from '@/constants'
import type {
  OutboundAnalysis,
  OutboundInfo,
  OutboundQuery,
  OutboundType,
  ProductOption,
} from '@/types'
import { formatDateTime, formatMoney, formatQty } from '@/utils/format'

const formRef = ref<FormInstance>()
const submitting = ref(false)

const productOptions = ref<ProductOption[]>([])
const optionsLoading = ref(false)

const form = reactive({
  product_id: undefined as number | undefined,
  outbound_type: 'sale' as OutboundType,
  quantity: 1,
  reason: '',
  remark: '',
})

const selectedProduct = computed(() =>
  productOptions.value.find((item) => item.id === form.product_id),
)

const rules = computed<FormRules>(() => ({
  product_id: [{ required: true, message: '请选择商品', trigger: 'change' }],
  outbound_type: [{ required: true, message: '请选择出库类型', trigger: 'change' }],
  quantity: [
    { required: true, message: '请输入出库数量', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (!value || value <= 0) {
          callback(new Error('出库数量必须大于 0'))
          return
        }
        if (selectedProduct.value && value > selectedProduct.value.stock_qty) {
          callback(new Error(`库存不足，当前可用 ${formatQty(selectedProduct.value.stock_qty)}`))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  reason: [
    {
      validator: (_rule, value, callback) => {
        if (form.outbound_type === 'loss' && !String(value || '').trim()) {
          callback(new Error('报损出库必须填写报损原因'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}))

async function searchProducts(keyword: string) {
  optionsLoading.value = true
  try {
    const { data } = await listProductOptions(keyword || undefined)
    productOptions.value = data
  } finally {
    optionsLoading.value = false
  }
}

function handleTypeChange() {
  formRef.value?.clearValidate('reason')
}

async function submit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const { data } = await createOutbound({
      product_id: form.product_id as number,
      outbound_type: form.outbound_type,
      quantity: form.quantity,
      reason: form.reason.trim() || null,
      remark: form.remark.trim() || null,
    })

    const batchInfo = data.items
      .map((item) => `${item.batch_no} 扣 ${formatQty(item.quantity)}`)
      .join('，')
    ElMessage.success(`出库成功，单号 ${data.order_no}（${batchInfo}）`)

    const product = selectedProduct.value
    if (product) {
      product.stock_qty = Math.max(0, product.stock_qty - form.quantity)
    }
    form.quantity = 1
    form.reason = ''
    form.remark = ''
    formRef.value.clearValidate()
    fetchRecords()
  } finally {
    submitting.value = false
  }
}

const records = ref<OutboundInfo[]>([])
const total = ref(0)
const listLoading = ref(false)
const listQuery = reactive<OutboundQuery>({
  page: 1,
  page_size: 10,
  keyword: '',
  outbound_type: undefined,
})

async function fetchRecords() {
  listLoading.value = true
  try {
    const { data } = await listOutbounds({
      ...listQuery,
      keyword: listQuery.keyword || undefined,
    })
    records.value = data.items
    total.value = data.total
  } finally {
    listLoading.value = false
  }
}

function handleSearchRecords() {
  listQuery.page = 1
  fetchRecords()
}

const exporting = ref(false)

async function handleExport() {
  exporting.value = true
  try {
    await downloadExport(
      'outbound',
      {
        keyword: listQuery.keyword || undefined,
        outbound_type: listQuery.outbound_type,
        start_date: listQuery.start_date,
        end_date: listQuery.end_date,
      },
      '出库记录.xlsx',
    )
    ElMessage.success('导出成功')
  } finally {
    exporting.value = false
  }
}

/* ---------- 出库分析图表 ---------- */
const analysis = ref<OutboundAnalysis>({
  days: 30,
  trend: [],
  type_distribution: [],
  top_products: [],
})

const hasTrendData = computed(() => analysis.value.trend.some((item) => item.quantity > 0))

const TYPE_COLOR: Record<string, string> = {
  sale: '#ffb020',
  loss: '#f56c6c',
}

const outboundTrendOption = computed<EChartsOption>(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    valueFormatter: (value) => formatQty(value as number),
  },
  grid: { left: 8, right: 14, top: 18, bottom: 4, containLabel: true },
  xAxis: {
    type: 'category',
    data: analysis.value.trend.map((item) => item.label.slice(5)),
    axisTick: { show: false },
    axisLine: { lineStyle: { color: '#e7edf6' } },
    axisLabel: { color: '#8493a8', fontSize: 10, interval: 4 },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f2f5fa' } },
    axisLabel: { color: '#8493a8', fontSize: 10 },
  },
  series: [
    {
      type: 'bar',
      barMaxWidth: 12,
      itemStyle: { color: '#ffb020', borderRadius: [4, 4, 0, 0] },
      data: analysis.value.trend.map((item) => item.quantity),
    },
  ],
}))

const typeOption = computed<EChartsOption>(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c}（{d}%）' },
  legend: { bottom: 0, itemWidth: 8, itemHeight: 8, textStyle: { fontSize: 10 } },
  series: [
    {
      type: 'pie',
      radius: ['46%', '68%'],
      center: ['50%', '42%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      data: analysis.value.type_distribution.map((item) => ({
        name: OUTBOUND_TYPE_LABEL[item.type] ?? item.type,
        value: item.quantity,
        itemStyle: { color: TYPE_COLOR[item.type] ?? '#c0c8d6' },
      })),
    },
  ],
}))

const topProductOption = computed<EChartsOption>(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 6, right: 42, top: 12, bottom: 4, containLabel: true },
  xAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f2f5fa' } },
    axisLabel: { color: '#8493a8', fontSize: 10 },
  },
  yAxis: {
    type: 'category',
    inverse: true,
    data: analysis.value.top_products.map((item) => item.name),
    axisTick: { show: false },
    axisLine: { show: false },
    axisLabel: { color: '#5a6b85', fontSize: 10, width: 92, overflow: 'truncate' },
  },
  series: [
    {
      type: 'bar',
      barMaxWidth: 11,
      itemStyle: { color: '#ffc46b', borderRadius: [0, 6, 6, 0] },
      label: {
        show: true,
        position: 'right',
        fontSize: 9,
        color: '#b08a4a',
        formatter: (params) => formatQty(Number(params.value)),
      },
      data: analysis.value.top_products.map((item) => item.quantity),
    },
  ],
}))

async function fetchAnalysis() {
  const { data } = await getOutboundAnalysis(30)
  analysis.value = data
}

onMounted(() => {
  searchProducts('')
  fetchRecords()
  fetchAnalysis()
})
</script>

<template>
  <div class="page-card">
    <div class="card-title">出库登记</div>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
      <el-row :gutter="16">
        <el-col :xs="24" :md="12">
          <el-form-item label="商品" prop="product_id">
            <el-select
              v-model="form.product_id"
              filterable
              remote
              reserve-keyword
              :remote-method="searchProducts"
              :loading="optionsLoading"
              placeholder="输入名称或条码搜索"
              style="width: 100%"
            >
              <el-option
                v-for="item in productOptions"
                :key="item.id"
                :label="`${item.name} (${item.barcode})`"
                :value="item.id"
                :disabled="item.stock_qty <= 0"
              >
                <span>{{ item.name }}</span>
                <span class="option-extra">
                  库存 {{ formatQty(item.stock_qty) }}
                  <template v-if="item.stock_qty <= 0">（无库存）</template>
                </span>
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :xs="24" :md="12">
          <el-form-item label="出库类型" prop="outbound_type">
            <el-radio-group v-model="form.outbound_type" @change="handleTypeChange">
              <el-radio value="sale">销售出库</el-radio>
              <el-radio value="loss">报损出库</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :xs="24" :md="12">
          <el-form-item label="出库数量" prop="quantity">
            <el-input-number
              v-model="form.quantity"
              :min="0.001"
              :precision="3"
              :step="1"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :xs="24" :md="12">
          <el-form-item v-if="form.outbound_type === 'loss'" label="报损原因" prop="reason">
            <el-input
              v-model="form.reason"
              maxlength="255"
              placeholder="必填，如 包装破损、超过保质期"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="24">
          <el-form-item label="当前库存">
            <span v-if="selectedProduct" class="stock-hint">
              {{ formatQty(selectedProduct.stock_qty) }} {{ selectedProduct.unit || '' }}
              <span class="hint">（按到期日由早到晚自动扣减批次）</span>
            </span>
            <span v-else class="hint">请先选择商品</span>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="备注">
        <el-input v-model="form.remark" maxlength="255" placeholder="选填" style="max-width: 420px" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="submit">提交出库</el-button>
        <el-button @click="formRef?.resetFields()">重置</el-button>
      </el-form-item>
    </el-form>
  </div>

  <el-row :gutter="16" style="margin-top: 16px">
    <el-col :xs="24" :md="8">
      <el-card shadow="never" header="近 30 天出库量" class="chart-card">
        <BaseChart v-if="hasTrendData" :option="outboundTrendOption" height="200px" />
        <el-empty v-else description="暂无出库数据" :image-size="60" />
      </el-card>
    </el-col>
    <el-col :xs="24" :md="8">
      <el-card shadow="never" header="出库类型构成" class="chart-card">
        <BaseChart
          v-if="analysis.type_distribution.length"
          :option="typeOption"
          height="200px"
        />
        <el-empty v-else description="暂无出库数据" :image-size="60" />
      </el-card>
    </el-col>
    <el-col :xs="24" :md="8">
      <el-card shadow="never" header="出库量 Top 8 商品" class="chart-card">
        <BaseChart
          v-if="analysis.top_products.length"
          :option="topProductOption"
          height="200px"
        />
        <el-empty v-else description="暂无出库数据" :image-size="60" />
      </el-card>
    </el-col>
  </el-row>

  <div class="page-card" style="margin-top: 16px">
    <div class="table-toolbar">
      <div class="card-title" style="margin: 0">出库记录</div>
      <div class="filter-bar">
        <el-select
          v-model="listQuery.outbound_type"
          placeholder="全部类型"
          clearable
          style="width: 140px"
          @change="handleSearchRecords"
        >
          <el-option label="销售出库" value="sale" />
          <el-option label="报损出库" value="loss" />
        </el-select>
        <el-input
          v-model="listQuery.keyword"
          placeholder="商品名称 / 条码"
          clearable
          style="width: 200px"
          @keyup.enter="handleSearchRecords"
          @clear="handleSearchRecords"
        />
        <el-button :loading="exporting" @click="handleExport">导出 Excel</el-button>
      </div>
    </div>

    <el-table v-loading="listLoading" :data="records" border stripe>
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="expand-block">
            <div class="expand-title">批次扣减明细</div>
            <el-table :data="row.items" size="small" border>
              <el-table-column prop="batch_no" label="批次号" width="160" />
              <el-table-column prop="production_date" label="生产日期" width="120" />
              <el-table-column prop="expiry_date" label="到期日" width="120" />
              <el-table-column label="数量" width="100" align="right">
                <template #default="scope">{{ formatQty(scope.row.quantity) }}</template>
              </el-table-column>
              <el-table-column label="成本价" width="100" align="right">
                <template #default="scope">{{ formatMoney(scope.row.cost_price) }}</template>
              </el-table-column>
              <el-table-column label="金额" width="120" align="right">
                <template #default="scope">{{ formatMoney(scope.row.amount) }}</template>
              </el-table-column>
            </el-table>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="order_no" label="单号" width="150" />
      <el-table-column prop="product_name" label="商品" min-width="160" show-overflow-tooltip />
      <el-table-column label="类型" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.outbound_type === 'sale' ? 'warning' : 'danger'" size="small">
            {{ row.outbound_type === 'sale' ? '销售' : '报损' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="数量" width="100" align="right">
        <template #default="{ row }">{{ formatQty(row.total_qty) }}</template>
      </el-table-column>
      <el-table-column label="成本金额" width="120" align="right">
        <template #default="{ row }">{{ formatMoney(row.total_amount) }}</template>
      </el-table-column>
      <el-table-column prop="reason" label="报损原因" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">{{ row.reason || '-' }}</template>
      </el-table-column>
      <el-table-column prop="operator_name" label="操作人" width="100" />
      <el-table-column label="出库时间" width="170">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
    </el-table>

    <div class="pagination-bar">
      <el-pagination
        v-model:current-page="listQuery.page"
        v-model:page-size="listQuery.page_size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="fetchRecords"
        @size-change="handleSearchRecords"
      />
    </div>
  </div>
</template>

<style scoped>
.card-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.option-extra {
  float: right;
  color: #909399;
  font-size: 12px;
}

.stock-hint {
  font-weight: 600;
  color: #303133;
}

.hint {
  color: #909399;
  font-size: 13px;
  font-weight: 400;
}

.filter-bar {
  display: flex;
  gap: 10px;
}

.chart-card {
  margin-bottom: 16px;
}

.expand-block {
  padding: 8px 16px 12px;
}

.expand-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}
</style>
