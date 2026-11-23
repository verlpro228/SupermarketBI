<script setup lang="ts">
import dayjs from 'dayjs'
import type { EChartsOption } from 'echarts'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { downloadExport } from '@/api/export'
import { createInbound, listInbounds } from '@/api/inbound'
import { listProductOptions } from '@/api/product'
import { getInboundAnalysis } from '@/api/stats'
import BaseChart from '@/components/common/BaseChart.vue'
import type { InboundAnalysis, InboundInfo, InboundQuery, ProductOption } from '@/types'
import { formatDateTime, formatQty } from '@/utils/format'

const formRef = ref<FormInstance>()
const submitting = ref(false)

const productOptions = ref<ProductOption[]>([])
const optionsLoading = ref(false)

const form = reactive({
  product_id: undefined as number | undefined,
  production_date: '',
  quantity: 1,
  cost_price: 0,
  supplier: '',
  remark: '',
})

const rules: FormRules = {
  product_id: [{ required: true, message: '请选择商品', trigger: 'change' }],
  production_date: [{ required: true, message: '请选择生产日期', trigger: 'change' }],
  quantity: [
    { required: true, message: '请输入入库数量', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (!value || value <= 0) {
          callback(new Error('入库数量必须大于 0'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  cost_price: [{ required: true, message: '请输入进价', trigger: 'blur' }],
}

const selectedProduct = computed(() =>
  productOptions.value.find((item) => item.id === form.product_id),
)

const expiryDate = computed(() => {
  if (!form.production_date || !selectedProduct.value) return ''
  return dayjs(form.production_date)
    .add(selectedProduct.value.shelf_life_days, 'day')
    .format('YYYY-MM-DD')
})

function disabledFutureDate(current: Date) {
  return current.getTime() > Date.now()
}

async function searchProducts(keyword: string) {
  optionsLoading.value = true
  try {
    const { data } = await listProductOptions(keyword || undefined)
    productOptions.value = data
  } finally {
    optionsLoading.value = false
  }
}

function handleProductChange(productId: number) {
  const product = productOptions.value.find((item) => item.id === productId)
  if (product && product.purchase_price !== null) {
    form.cost_price = product.purchase_price
  }
}

async function submit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const { data } = await createInbound({
      product_id: form.product_id as number,
      quantity: form.quantity,
      cost_price: form.cost_price,
      production_date: form.production_date,
      supplier: form.supplier.trim() || null,
      remark: form.remark.trim() || null,
    })
    ElMessage.success(`入库成功，单号 ${data.order_no}`)
    form.quantity = 1
    form.cost_price = 0
    form.supplier = ''
    form.remark = ''
    formRef.value.clearValidate()
    fetchRecords()
  } finally {
    submitting.value = false
  }
}

const records = ref<InboundInfo[]>([])
const total = ref(0)
const listLoading = ref(false)
const listQuery = reactive<InboundQuery>({
  page: 1,
  page_size: 10,
  keyword: '',
})

async function fetchRecords() {
  listLoading.value = true
  try {
    const { data } = await listInbounds({ ...listQuery, keyword: listQuery.keyword || undefined })
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
      'inbound',
      {
        keyword: listQuery.keyword || undefined,
        start_date: listQuery.start_date,
        end_date: listQuery.end_date,
      },
      '入库记录.xlsx',
    )
    ElMessage.success('导出成功')
  } finally {
    exporting.value = false
  }
}

/* ---------- 入库分析图表 ---------- */
const analysis = ref<InboundAnalysis>({
  days: 30,
  trend: [],
  supplier_ranking: [],
  category_distribution: [],
})

const hasTrendData = computed(() => analysis.value.trend.some((item) => item.quantity > 0))

const inboundTrendOption = computed<EChartsOption>(() => ({
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
      itemStyle: { color: '#5b9bff', borderRadius: [4, 4, 0, 0] },
      data: analysis.value.trend.map((item) => item.quantity),
    },
  ],
}))

const supplierOption = computed<EChartsOption>(() => ({
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
    data: analysis.value.supplier_ranking.map((item) => item.supplier),
    axisTick: { show: false },
    axisLine: { show: false },
    axisLabel: { color: '#5a6b85', fontSize: 10, width: 92, overflow: 'truncate' },
  },
  series: [
    {
      type: 'bar',
      barMaxWidth: 11,
      itemStyle: { color: '#7aa9ff', borderRadius: [0, 6, 6, 0] },
      label: {
        show: true,
        position: 'right',
        fontSize: 9,
        color: '#8794a8',
        formatter: (params) => formatQty(Number(params.value)),
      },
      data: analysis.value.supplier_ranking.map((item) => item.quantity),
    },
  ],
}))

const inboundCategoryOption = computed<EChartsOption>(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c}（{d}%）' },
  legend: {
    bottom: 0,
    width: '94%',
    itemWidth: 8,
    itemHeight: 8,
    itemGap: 8,
    textStyle: { fontSize: 10 },
  },
  series: [
    {
      type: 'pie',
      radius: ['44%', '66%'],
      center: ['50%', '40%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      data: analysis.value.category_distribution.map((item) => ({
        name: item.category,
        value: item.quantity,
      })),
    },
  ],
}))

async function fetchAnalysis() {
  const { data } = await getInboundAnalysis(30)
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
    <div class="card-title">入库登记</div>

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
              @change="handleProductChange"
            >
              <el-option
                v-for="item in productOptions"
                :key="item.id"
                :label="`${item.name} (${item.barcode})`"
                :value="item.id"
              >
                <span>{{ item.name }}</span>
                <span class="option-extra">{{ item.barcode }}</span>
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :xs="24" :md="12">
          <el-form-item label="生产日期" prop="production_date">
            <el-date-picker
              v-model="form.production_date"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="请选择生产日期"
              :disabled-date="disabledFutureDate"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :xs="24" :md="12">
          <el-form-item label="入库数量" prop="quantity">
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
          <el-form-item label="进价" prop="cost_price">
            <el-input-number
              v-model="form.cost_price"
              :min="0"
              :precision="2"
              :step="0.1"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :xs="24" :md="12">
          <el-form-item label="供应商">
            <el-input v-model="form.supplier" maxlength="128" placeholder="选填" />
          </el-form-item>
        </el-col>

        <el-col :xs="24" :md="12">
          <el-form-item label="备注">
            <el-input v-model="form.remark" maxlength="255" placeholder="选填" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="24">
          <el-form-item label="到期日">
            <div class="expiry-preview">
              <el-tag v-if="expiryDate" type="warning" effect="plain">{{ expiryDate }}</el-tag>
              <span v-else class="hint">选择商品与生产日期后自动计算</span>
              <span v-if="selectedProduct" class="hint">
                保质期 {{ selectedProduct.shelf_life_days }} 天，当前库存
                {{ formatQty(selectedProduct.stock_qty) }}
              </span>
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="submit">提交入库</el-button>
        <el-button @click="formRef?.resetFields()">重置</el-button>
      </el-form-item>
    </el-form>
  </div>

  <el-row :gutter="16" style="margin-top: 16px">
    <el-col :xs="24" :md="8">
      <el-card shadow="never" header="近 30 天入库量" class="chart-card">
        <BaseChart v-if="hasTrendData" :option="inboundTrendOption" height="200px" />
        <el-empty v-else description="暂无入库数据" :image-size="60" />
      </el-card>
    </el-col>
    <el-col :xs="24" :md="8">
      <el-card shadow="never" header="供应商供货量 Top 8" class="chart-card">
        <BaseChart
          v-if="analysis.supplier_ranking.length"
          :option="supplierOption"
          height="200px"
        />
        <el-empty v-else description="暂无供应商数据" :image-size="60" />
      </el-card>
    </el-col>
    <el-col :xs="24" :md="8">
      <el-card shadow="never" header="入库品类占比" class="chart-card">
        <BaseChart
          v-if="analysis.category_distribution.length"
          :option="inboundCategoryOption"
          height="200px"
        />
        <el-empty v-else description="暂无品类数据" :image-size="60" />
      </el-card>
    </el-col>
  </el-row>

  <div class="page-card" style="margin-top: 16px">
    <div class="table-toolbar">
      <div class="card-title" style="margin: 0">入库记录</div>
      <div class="filter-bar">
        <el-input
          v-model="listQuery.keyword"
          placeholder="商品名称 / 条码"
          clearable
          style="width: 220px"
          @keyup.enter="handleSearchRecords"
          @clear="handleSearchRecords"
        />
        <el-button :loading="exporting" @click="handleExport">导出 Excel</el-button>
      </div>
    </div>

    <el-table v-loading="listLoading" :data="records" border stripe>
      <el-table-column prop="order_no" label="单号" width="150" />
      <el-table-column prop="product_name" label="商品" min-width="160" show-overflow-tooltip />
      <el-table-column prop="batch_no" label="批次号" width="150" show-overflow-tooltip />
      <el-table-column label="数量" width="100" align="right">
        <template #default="{ row }">{{ formatQty(row.quantity) }}</template>
      </el-table-column>
      <el-table-column label="进价" width="90" align="right">
        <template #default="{ row }">{{ formatQty(row.cost_price) }}</template>
      </el-table-column>
      <el-table-column label="金额" width="110" align="right">
        <template #default="{ row }">{{ formatQty(row.amount) }}</template>
      </el-table-column>
      <el-table-column prop="production_date" label="生产日期" width="110" />
      <el-table-column prop="expiry_date" label="到期日" width="110" />
      <el-table-column prop="supplier" label="供应商" width="130" show-overflow-tooltip>
        <template #default="{ row }">{{ row.supplier || '-' }}</template>
      </el-table-column>
      <el-table-column prop="operator_name" label="操作人" width="100" />
      <el-table-column label="入库时间" width="170">
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

.expiry-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.hint {
  color: #909399;
  font-size: 13px;
}

.filter-bar {
  display: flex;
  gap: 10px;
}

.chart-card {
  margin-bottom: 16px;
}
</style>
