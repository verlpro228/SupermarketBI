<script setup lang="ts">
import type { EChartsOption } from 'echarts'
import { computed, onMounted, ref, watch } from 'vue'

import { getDashboard } from '@/api/stats'
import BaseChart from '@/components/common/BaseChart.vue'
import { EXPIRY_LEVEL_LABEL } from '@/constants'
import { useUserStore } from '@/stores/user'
import type {
  CategoryFlowItem,
  CategoryValue,
  DashboardKpi,
  ExpiryLevelCount,
  LowStockItem,
  ProductValueItem,
  TrendPoint,
} from '@/types'
import { formatMoney, formatQty } from '@/utils/format'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin)

const LEVEL_COLOR: Record<string, string> = {
  expired: '#f56c6c',
  urgent: '#ffb020',
  warning: '#5b9bff',
}

const loading = ref(false)
const days = ref(30)

const kpi = ref<DashboardKpi>({
  product_count: 0,
  total_stock: 0,
  stock_value: null,
  expiry_count: 0,
})
const trend = ref<TrendPoint[]>([])
const categoryValue = ref<CategoryValue[]>([])
const categoryFlow = ref<CategoryFlowItem[]>([])
const expiryDistribution = ref<ExpiryLevelCount[]>([])
const topValueProducts = ref<ProductValueItem[]>([])
const lowStockProducts = ref<LowStockItem[]>([])

const cards = computed(() => {
  const list = [
    {
      key: 'product',
      label: '商品总数',
      value: formatQty(kpi.value.product_count),
      icon: 'Goods',
      color: '#5b9bff',
    },
    {
      key: 'stock',
      label: '库存总量',
      value: formatQty(kpi.value.total_stock),
      icon: 'Box',
      color: '#67c23a',
    },
  ]

  if (isAdmin.value) {
    list.push({
      key: 'value',
      label: '库存货值',
      value: formatMoney(kpi.value.stock_value),
      icon: 'Money',
      color: '#e6a23c',
    })
  }

  list.push({
    key: 'expiry',
    label: '临期商品数',
    value: formatQty(kpi.value.expiry_count),
    icon: 'AlarmClock',
    color: '#f56c6c',
  })

  return list
})

/* ---------- 1. 出入库趋势 ---------- */
const trendOption = computed<EChartsOption>(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['入库量', '出库量'], top: 0, itemWidth: 12, itemHeight: 8 },
  grid: { left: 12, right: 24, top: 44, bottom: 10, containLabel: true },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: trend.value.map((item) => item.label),
    axisTick: { show: false },
    axisLine: { lineStyle: { color: '#e7edf6' } },
    axisLabel: {
      color: '#8493a8',
      fontSize: 11,
      formatter: (value: string) => value.slice(5),
      rotate: trend.value.length > 45 ? 45 : 0,
    },
  },
  yAxis: {
    type: 'value',
    name: '数量',
    nameTextStyle: { color: '#8493a8', fontSize: 11 },
    splitLine: { lineStyle: { color: '#f2f5fa' } },
    axisLabel: { color: '#8493a8', fontSize: 11 },
  },
  series: [
    {
      name: '入库量',
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: trend.value.map((item) => item.inbound),
      itemStyle: { color: '#5b9bff' },
      areaStyle: { color: 'rgba(91,155,255,0.14)' },
    },
    {
      name: '出库量',
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: trend.value.map((item) => item.outbound),
      itemStyle: { color: '#ffb020' },
      areaStyle: { color: 'rgba(255,176,32,0.14)' },
    },
  ],
}))

/* ---------- 2. 分类库存货值占比 ---------- */
const pieOption = computed<EChartsOption>(() => ({
  tooltip: {
    trigger: 'item',
    formatter: (params) => {
      const data = params as { name: string; value: number; percent: number }
      return `${data.name}<br/>${formatMoney(data.value)}（${data.percent}%）`
    },
  },
  legend: {
    bottom: 0,
    width: '92%',
    itemWidth: 9,
    itemHeight: 9,
    itemGap: 10,
    textStyle: { fontSize: 11 },
  },
  series: [
    {
      type: 'pie',
      radius: ['44%', '68%'],
      center: ['50%', '42%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
      label: { show: false },
      data: categoryValue.value.map((item) => ({
        name: item.category,
        value: item.value,
      })),
    },
  ],
}))

/* ---------- 3. 分类出入库对比 ---------- */
const flowOption = computed<EChartsOption>(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  legend: { data: ['入库量', '出库量'], top: 0, itemWidth: 12, itemHeight: 8 },
  grid: { left: 10, right: 20, top: 44, bottom: 6, containLabel: true },
  xAxis: {
    type: 'category',
    data: categoryFlow.value.map((item) => item.category),
    axisTick: { show: false },
    axisLine: { lineStyle: { color: '#e7edf6' } },
    axisLabel: { color: '#8493a8', fontSize: 11 },
  },
  // 入库与出库量级差距大，用双轴保证两边都看得清
  yAxis: [
    {
      type: 'value',
      name: '入库',
      nameTextStyle: { color: '#8493a8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f2f5fa' } },
      axisLabel: { color: '#8493a8', fontSize: 11 },
    },
    {
      type: 'value',
      name: '出库',
      nameTextStyle: { color: '#8493a8', fontSize: 11 },
      splitLine: { show: false },
      axisLabel: { color: '#8493a8', fontSize: 11 },
    },
  ],
  series: [
    {
      name: '入库量',
      type: 'bar',
      yAxisIndex: 0,
      barMaxWidth: 20,
      itemStyle: { color: '#5b9bff', borderRadius: [6, 6, 0, 0] },
      data: categoryFlow.value.map((item) => item.inbound),
    },
    {
      name: '出库量',
      type: 'bar',
      yAxisIndex: 1,
      barMaxWidth: 20,
      itemStyle: { color: '#ffb020', borderRadius: [6, 6, 0, 0] },
      data: categoryFlow.value.map((item) => item.outbound),
    },
  ],
}))

/* ---------- 4. 临期批次分档 ---------- */
const expiryOption = computed<EChartsOption>(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} 个批次（{d}%）' },
  legend: { bottom: 0, itemWidth: 10, itemHeight: 10 },
  series: [
    {
      type: 'pie',
      radius: ['52%', '74%'],
      center: ['50%', '44%'],
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
      label: { show: false },
      data: expiryDistribution.value.map((item) => ({
        name: EXPIRY_LEVEL_LABEL[item.level] ?? item.level,
        value: item.count,
        itemStyle: { color: LEVEL_COLOR[item.level] ?? '#c0c8d6' },
      })),
    },
  ],
}))

/* ---------- 5. 库存货值 Top 10 ---------- */
const valueOption = computed<EChartsOption>(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    valueFormatter: (value) => formatMoney(value as number),
  },
  grid: { left: 6, right: 62, top: 10, bottom: 6, containLabel: true },
  xAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f2f5fa' } },
    axisLabel: { color: '#8493a8', fontSize: 11 },
  },
  yAxis: {
    type: 'category',
    inverse: true,
    data: topValueProducts.value.map((item) => item.name),
    axisTick: { show: false },
    axisLine: { show: false },
    axisLabel: { color: '#5a6b85', fontSize: 11, width: 92, overflow: 'truncate' },
  },
  series: [
    {
      type: 'bar',
      barMaxWidth: 14,
      itemStyle: { color: '#7aa9ff', borderRadius: [0, 7, 7, 0] },
      label: {
        show: true,
        position: 'right',
        color: '#8794a8',
        fontSize: 10,
        formatter: (params) => formatMoney(Number(params.value)),
      },
      data: topValueProducts.value.map((item) => item.value),
    },
  ],
}))

/* ---------- 6. 低库存缺口 Top 10 ---------- */
const lowStockOption = computed<EChartsOption>(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    valueFormatter: (value) => `${formatQty(value as number)}`,
  },
  grid: { left: 6, right: 52, top: 10, bottom: 6, containLabel: true },
  xAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f2f5fa' } },
    axisLabel: { color: '#8493a8', fontSize: 11 },
  },
  yAxis: {
    type: 'category',
    inverse: true,
    data: lowStockProducts.value.map((item) => item.name),
    axisTick: { show: false },
    axisLine: { show: false },
    axisLabel: { color: '#5a6b85', fontSize: 11, width: 92, overflow: 'truncate' },
  },
  series: [
    {
      type: 'bar',
      barMaxWidth: 14,
      itemStyle: { color: '#ff9d8f', borderRadius: [0, 7, 7, 0] },
      label: {
        show: true,
        position: 'right',
        color: '#c9705f',
        fontSize: 10,
        formatter: (params) => formatQty(Number(params.value)),
      },
      data: lowStockProducts.value.map((item) => item.gap),
    },
  ],
}))

const isEmptyPie = computed(() => categoryValue.value.length === 0)

async function fetchData() {
  loading.value = true
  try {
    const { data } = await getDashboard(days.value)
    kpi.value = data.kpi
    trend.value = data.trend
    categoryValue.value = data.category_value
    categoryFlow.value = data.category_flow
    expiryDistribution.value = data.expiry_distribution
    topValueProducts.value = data.top_value_products
    lowStockProducts.value = data.low_stock_products
  } finally {
    loading.value = false
  }
}

watch(days, fetchData)
onMounted(fetchData)
</script>

<template>
  <div v-loading="loading">
    <div class="header-bar">
      <div>
        <div class="page-title">数据看板</div>
        <div class="page-sub">
          {{
            isAdmin
              ? '库存整体概览与流动趋势'
              : '库存整体概览（金额类指标对库管员隐藏）'
          }}
        </div>
      </div>
      <el-radio-group v-model="days">
        <el-radio-button :value="7">近 7 天</el-radio-button>
        <el-radio-button :value="30">近 30 天</el-radio-button>
        <el-radio-button :value="90">近 90 天</el-radio-button>
      </el-radio-group>
    </div>

    <el-row :gutter="16">
      <el-col v-for="card in cards" :key="card.key" :xs="12" :md="24 / cards.length">
        <el-card shadow="never" class="kpi-card">
          <div class="kpi-inner">
            <div>
              <div class="kpi-label">{{ card.label }}</div>
              <div class="kpi-value">{{ card.value }}</div>
            </div>
            <el-icon :size="34" :color="card.color">
              <component :is="card.icon" />
            </el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第一组：趋势 + 分类货值 -->
    <el-row :gutter="16">
      <el-col :xs="24" :md="isAdmin ? 16 : 24">
        <el-card shadow="never" header="出入库趋势" class="chart-card">
          <BaseChart :option="trendOption" height="320px" />
        </el-card>
      </el-col>
      <el-col v-if="isAdmin" :xs="24" :md="8">
        <el-card shadow="never" header="分类库存货值占比" class="chart-card">
          <BaseChart v-if="!isEmptyPie" :option="pieOption" height="320px" />
          <el-empty v-else description="暂无库存数据" :image-size="70" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 第二组：分类出入库对比 + 临期分档 -->
    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never" header="分类出入库对比" class="chart-card">
          <BaseChart v-if="categoryFlow.length" :option="flowOption" height="300px" />
          <el-empty v-else description="所选区间暂无出入库记录" :image-size="70" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never" header="临期批次分档" class="chart-card">
          <BaseChart
            v-if="expiryDistribution.length"
            :option="expiryOption"
            height="300px"
          />
          <el-empty v-else description="暂无临期批次" :image-size="70" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 第三组：货值排行 + 低库存排行 -->
    <el-row :gutter="16">
      <el-col v-if="isAdmin" :xs="24" :md="12">
        <el-card shadow="never" header="库存货值 Top 10 商品" class="chart-card">
          <BaseChart
            v-if="topValueProducts.length"
            :option="valueOption"
            height="320px"
          />
          <el-empty v-else description="暂无库存数据" :image-size="70" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="isAdmin ? 12 : 24">
        <el-card shadow="never" header="低库存缺口 Top 10" class="chart-card">
          <BaseChart
            v-if="lowStockProducts.length"
            :option="lowStockOption"
            height="320px"
          />
          <el-empty v-else description="库存充足，暂无低库存商品" :image-size="70" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped lang="scss">
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1b2a41;
}

.page-sub {
  color: #8b98ac;
  font-size: 13px;
  margin-top: 4px;
}

.kpi-card {
  margin-bottom: 16px;
}

.chart-card {
  margin-bottom: 16px;
}

.kpi-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.kpi-label {
  color: #8b98ac;
  font-size: 13px;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 26px;
  font-weight: 600;
  color: #1b2a41;
}
</style>
