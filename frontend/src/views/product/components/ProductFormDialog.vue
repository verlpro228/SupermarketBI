<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { computed, reactive, ref, watch } from 'vue'

import { createProduct, updateProduct } from '@/api/product'
import type { CategoryOption, ProductInfo } from '@/types'

const visible = defineModel<boolean>({ required: true })

const props = defineProps<{
  product?: ProductInfo | null
  categories: CategoryOption[]
}>()

const emit = defineEmits<{ success: [] }>()

const isEdit = computed(() => Boolean(props.product?.id))
const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = reactive({
  barcode: '',
  name: '',
  category_id: undefined as number | undefined,
  spec: '',
  unit: '',
  purchase_price: 0,
  sale_price: 0,
  safe_stock: 0,
  shelf_life_days: 0,
})

const rules: FormRules = {
  barcode: [
    { required: true, message: '请输入条码', trigger: 'blur' },
    { max: 64, message: '不能超过 64 个字符', trigger: 'blur' },
  ],
  name: [
    { required: true, message: '请输入商品名称', trigger: 'blur' },
    { max: 128, message: '不能超过 128 个字符', trigger: 'blur' },
  ],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

watch(visible, (opened) => {
  if (!opened) return
  const current = props.product
  form.barcode = current?.barcode ?? ''
  form.name = current?.name ?? ''
  form.category_id = current?.category_id
  form.spec = current?.spec ?? ''
  form.unit = current?.unit ?? ''
  form.purchase_price = current?.purchase_price ?? 0
  form.sale_price = current?.sale_price ?? 0
  form.safe_stock = current?.safe_stock ?? 0
  form.shelf_life_days = current?.shelf_life_days ?? 0
  formRef.value?.clearValidate()
})

async function submit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  const payload = {
    barcode: form.barcode.trim(),
    name: form.name.trim(),
    category_id: form.category_id as number,
    spec: form.spec.trim() || null,
    unit: form.unit.trim() || null,
    purchase_price: form.purchase_price,
    sale_price: form.sale_price,
    safe_stock: form.safe_stock,
    shelf_life_days: form.shelf_life_days,
  }

  submitting.value = true
  try {
    if (isEdit.value && props.product) {
      await updateProduct(props.product.id, payload)
      ElMessage.success('保存成功')
    } else {
      await createProduct(payload)
      ElMessage.success('新增成功')
    }
    visible.value = false
    emit('success')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog v-model="visible" :title="isEdit ? '编辑商品' : '新增商品'" width="620px">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="条码" prop="barcode">
            <el-input v-model="form.barcode" maxlength="64" placeholder="商品条码" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="商品名称" prop="name">
            <el-input v-model="form.name" maxlength="128" placeholder="商品名称" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="所属分类" prop="category_id">
            <el-select v-model="form.category_id" placeholder="请选择" style="width: 100%">
              <el-option
                v-for="item in props.categories"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="规格">
            <el-input v-model="form.spec" maxlength="64" placeholder="如 250ml*24盒" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="单位">
            <el-input v-model="form.unit" maxlength="16" placeholder="箱 / 瓶 / kg" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="保质期天数">
            <el-input-number
              v-model="form.shelf_life_days"
              :min="0"
              :max="3650"
              :precision="0"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="进价">
            <el-input-number
              v-model="form.purchase_price"
              :min="0"
              :precision="2"
              :step="0.1"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="售价">
            <el-input-number
              v-model="form.sale_price"
              :min="0"
              :precision="2"
              :step="0.1"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="安全库存">
        <el-input-number
          v-model="form.safe_stock"
          :min="0"
          :precision="3"
          :step="1"
          controls-position="right"
          style="width: 200px"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
    </template>
  </el-dialog>
</template>
