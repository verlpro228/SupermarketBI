<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { ref, watch } from 'vue'

import { createExpiryLoss } from '@/api/expiry'
import type { ExpiryBatch } from '@/types'
import { formatQty } from '@/utils/format'

const visible = defineModel<boolean>({ required: true })

const props = defineProps<{
  batches: ExpiryBatch[]
}>()

const emit = defineEmits<{ success: [] }>()

interface LossRow {
  batch_id: number
  batch_no: string
  product_name: string
  unit: string | null
  max: number
  quantity: number
}

const rows = ref<LossRow[]>([])
const reason = ref('临期报损')
const submitting = ref(false)

watch(visible, (opened) => {
  if (!opened) return
  rows.value = props.batches.map((item) => ({
    batch_id: item.batch_id,
    batch_no: item.batch_no,
    product_name: item.product_name,
    unit: item.unit,
    max: item.qty_remaining,
    quantity: item.qty_remaining,
  }))
  reason.value = '临期报损'
})

async function submit() {
  const items = rows.value
    .filter((row) => row.quantity > 0)
    .map((row) => ({ batch_id: row.batch_id, quantity: row.quantity }))

  if (items.length === 0) {
    ElMessage.warning('请至少填写一个批次的报损数量')
    return
  }
  if (!reason.value.trim()) {
    ElMessage.warning('请填写报损原因')
    return
  }

  const invalid = rows.value.find((row) => row.quantity > row.max)
  if (invalid) {
    ElMessage.warning(`批次 ${invalid.batch_no} 报损数量不能超过剩余 ${formatQty(invalid.max)}`)
    return
  }

  submitting.value = true
  try {
    const { data } = await createExpiryLoss({ items, reason: reason.value.trim() })
    ElMessage.success(`已完成 ${data.count} 个批次报损`)
    visible.value = false
    emit('success')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog v-model="visible" title="临期报损" width="680px">
    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="报损将生成报损出库单，并同步扣减批次与商品库存，不可撤销"
      style="margin-bottom: 16px"
    />

    <el-table :data="rows" border size="small">
      <el-table-column prop="product_name" label="商品" min-width="140" show-overflow-tooltip />
      <el-table-column prop="batch_no" label="批次号" width="150" show-overflow-tooltip />
      <el-table-column label="剩余" width="90" align="right">
        <template #default="{ row }">{{ formatQty(row.max) }}</template>
      </el-table-column>
      <el-table-column label="报损数量" width="160" align="center">
        <template #default="{ row }">
          <el-input-number
            v-model="row.quantity"
            :min="0"
            :max="row.max"
            :precision="3"
            :step="1"
            size="small"
            controls-position="right"
            style="width: 130px"
          />
        </template>
      </el-table-column>
    </el-table>

    <el-form label-width="88px" style="margin-top: 16px">
      <el-form-item label="报损原因">
        <el-input v-model="reason" maxlength="255" show-word-limit />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="danger" :loading="submitting" @click="submit">确认报损</el-button>
    </template>
  </el-dialog>
</template>
