<script setup lang="ts">
import type { EChartsOption } from 'echarts'
import { computed, onMounted, ref, watch } from 'vue'

import { getTrend } from '@/api/stats'
import BaseChart from '@/components/common/BaseChart.vue'
import type { TrendGranularity, TrendPoint } from '@/types'
import { formatQty } from '@/utils/format'

const loading = ref(false)
const days = ref(30)
const granularity = ref<TrendGranularity>('day')
const items = ref<TrendPoint[]>([])

const totalInbound = computed(() =>
  items.value.reduce((sum, item) => sum + item.inbound, 0),
)
const totalOutbound = computed(() =>
  items.value.reduce((sum, item) => sum + item.outbound, 0),
)
const netChange = computed(() => totalInbound.value - totalOutbound.value)

const chartOption = computed<EChartsOption>(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['入库量', '出库量'], top: 0 },
  grid: { left: 56, right: 24, top: 44, bottom: 48 },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: items.value.map((item) => item.label),
    axisLabel: {
      formatter: (value: string) =>
        granularity.value === 'day' ? value.slice(5) : value,
      rotate: items.value.length > 45 ? 45 : 0,
    },
  },
  yAxis: { type: 'value', name: '数量' },
  series: [
    {
      name: '入库量',
      type: 'line',
      smooth: true,
      showSymbol: items.value.length <= 31,
      data: items.value.map((item) => item.inbound),
      itemStyle: { color: '#409EFF' },
      areaStyle: { color: 'rgba(64,158,255,0.12)' },
    },
    {
      name: '出库量',
      type: 'line',
      smooth: true,
      showSymbol: items.value.length <= 31,
      data: items.value.map((item) => item.outbound),
      itemStyle: { color: '#E6A23C' },
      areaStyle: { color: 'rgba(230,162,60,0.12)' },
    },
  ],
}))

async function fetchData() {
  loading.value = true
  try {
    const { data } = await getTrend({ days: days.value, granularity: granularity.value })
    items.value = data.items
  } finally {
    loading.value = false
  }
}

watch([days, granularity], fetchData)
onMounted(fetchData)
</script>

<template>
  <div class="page-card" v-loading="loading">
    <div class="table-toolbar">
      <div>
        <div class="card-title">出入库趋势</div>
        <div class="hint">按{{ granularity === 'day' ? '日' : '月' }}对比入库与出库数量走势</div>
      </div>
      <div class="filters">
        <el-radio-group v-model="granularity">
          <el-radio-button value="day">按日</el-radio-button>
          <el-radio-button value="month">按月</el-radio-button>
        </el-radio-group>
        <el-radio-group v-model="days">
          <el-radio-button :value="30">近 30 天</el-radio-button>
          <el-radio-button :value="90">近 90 天</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <el-row :gutter="16" style="margin-bottom: 8px">
      <el-col :xs="24" :sm="8">
        <div class="summary-item">
          <span class="summary-label">区间入库总量</span>
          <span class="summary-value inbound">{{ formatQty(totalInbound) }}</span>
        </div>
      </el-col>
      <el-col :xs="24" :sm="8">
        <div class="summary-item">
          <span class="summary-label">区间出库总量</span>
          <span class="summary-value outbound">{{ formatQty(totalOutbound) }}</span>
        </div>
      </el-col>
      <el-col :xs="24" :sm="8">
        <div class="summary-item">
          <span class="summary-label">净变化</span>
          <span class="summary-value" :class="netChange >= 0 ? 'inbound' : 'outbound'">
            {{ netChange >= 0 ? '+' : '' }}{{ formatQty(netChange) }}
          </span>
        </div>
      </el-col>
    </el-row>

    <BaseChart :option="chartOption" height="380px" />
  </div>
</template>

<style scoped>
.card-title {
  font-size: 16px;
  font-weight: 600;
}

.hint {
  color: #909399;
  font-size: 13px;
  margin-top: 4px;
}

.filters {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f7f9fc;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
}

.summary-label {
  color: #909399;
  font-size: 13px;
}

.summary-value {
  font-size: 20px;
  font-weight: 600;
}

.summary-value.inbound {
  color: #409eff;
}

.summary-value.outbound {
  color: #e6a23c;
}
</style>
