<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { reactive, ref, watch } from 'vue'

import { adjustStock, listStockBatches } from '@/api/stock'
import type { StockBatch, StockInfo } from '@/types'
import { formatDaysLeft, formatQty } from '@/utils/format'

const visible = defineModel<boolean>({ required: true })

const props = defineProps<{
  product?: StockInfo | null
}>()

const emit = defineEmits<{ success: [] }>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const batchLoading = ref(false)
const batches = ref<StockBatch[]>([])

const form = reactive({
  batch_id: undefined as number | undefined,
  new_qty: 0,
  reason: '',
})

const rules: FormRules = {
  batch_id: [{ required: true, message: '请选择批次', trigger: 'change' }],
  new_qty: [{ required: true, message: '请输入调整后数量', trigger: 'blur' }],
  reason: [
    { required: true, message: '请填写调整原因', trigger: 'blur' },
    { max: 255, message: '不能超过 255 个字符', trigger: 'blur' },
  ],
}

const selectedBatch = () => batches.value.find((item) => item.batch_id === form.batch_id)

watch(visible, async (opened) => {
  if (!opened || !props.product) return

  form.reason = ''
  form.batch_id = undefined
  form.new_qty = 0
  batches.value = []
  formRef.value?.clearValidate()

  batchLoading.value = true
  try {
    const { data } = await listStockBatches(props.product.product_id)
    batches.value = data
    if (data.length > 0) {
      form.batch_id = data[0].batch_id
      form.new_qty = data[0].qty_remaining
    }
  } finally {
    batchLoading.value = false
  }
})

watch(
  () => form.batch_id,
  (batchId) => {
    const batch = batches.value.find((item) => item.batch_id === batchId)
    if (batch) {
      form.new_qty = batch.qty_remaining
    }
  },
)

async function submit() {
  if (!formRef.value || !props.product) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await adjustStock({
      product_id: props.product.product_id,
      batch_id: form.batch_id as number,
      new_qty: form.new_qty,
      reason: form.reason.trim(),
    })
    ElMessage.success('库存已调整')
    visible.value = false
    emit('success')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog v-model="visible" title="调整库存" width="560px">
    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="调整会直接改写批次剩余数量并记录操作人，请谨慎操作"
      style="margin-bottom: 16px"
    />

    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="商品">
        <span>{{ props.product?.name }}（{{ props.product?.barcode }}）</span>
      </el-form-item>

      <el-form-item label="调整批次" prop="batch_id">
        <el-select
          v-model="form.batch_id"
          :loading="batchLoading"
          placeholder="请选择批次"
          style="width: 100%"
        >
          <el-option
            v-for="item in batches"
            :key="item.batch_id"
            :label="`${item.batch_no} | 到期 ${item.expiry_date} | 剩余 ${formatQty(item.qty_remaining)}`"
            :value="item.batch_id"
          />
        </el-select>
      </el-form-item>

      <el-form-item v-if="selectedBatch()" label="当前信息">
        <span class="hint">
          剩余 {{ formatQty(selectedBatch()?.qty_remaining) }}，到期
          {{ selectedBatch()?.expiry_date }}（{{ formatDaysLeft(selectedBatch()?.days_left) }}）
        </span>
      </el-form-item>

      <el-form-item label="调整后数量" prop="new_qty">
        <el-input-number
          v-model="form.new_qty"
          :min="0"
          :precision="3"
          :step="1"
          controls-position="right"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="调整原因" prop="reason">
        <el-input
          v-model="form.reason"
          type="textarea"
          :rows="3"
          maxlength="255"
          show-word-limit
          placeholder="如：盘点差异、破损核销"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">确定调整</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.hint {
  color: #909399;
  font-size: 13px;
}
</style>
