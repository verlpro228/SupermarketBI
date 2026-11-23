<script setup lang="ts">
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
} from 'echarts/components'
import { init, use, type ECharts } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
])

const props = withDefaults(
  defineProps<{
    option: EChartsOption
    height?: string
  }>(),
  { height: '320px' },
)

const container = ref<HTMLDivElement>()
let chart: ECharts | null = null
let observer: ResizeObserver | null = null

onMounted(() => {
  if (!container.value) return
  chart = init(container.value)
  chart.setOption(props.option)

  observer = new ResizeObserver(() => chart?.resize())
  observer.observe(container.value)
})

watch(
  () => props.option,
  (option) => {
    chart?.setOption(option, true)
  },
  { deep: true },
)

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div ref="container" :style="{ width: '100%', height: props.height }" />
</template>
