<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { listCategories } from '@/api/category'
import { listProducts, updateProductStatus } from '@/api/product'
import { useUserStore } from '@/stores/user'
import type { CategoryInfo, ProductInfo, ProductListQuery } from '@/types'
import { formatQty } from '@/utils/format'

import CategoryManageDialog from './components/CategoryManageDialog.vue'
import ProductFormDialog from './components/ProductFormDialog.vue'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin)

const loading = ref(false)
const rows = ref<ProductInfo[]>([])
const total = ref(0)
const categories = ref<CategoryInfo[]>([])

const activeCategories = computed(() => categories.value.filter((item) => item.status === 1))

const query = reactive<ProductListQuery>({
  page: 1,
  page_size: 20,
  keyword: '',
  category_id: undefined,
  status: undefined,
})

const formVisible = ref(false)
const editingProduct = ref<ProductInfo | null>(null)
const categoryVisible = ref(false)

async function fetchList() {
  loading.value = true
  try {
    const { data } = await listProducts({ ...query, keyword: query.keyword || undefined })
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

function handleCreate() {
  editingProduct.value = null
  formVisible.value = true
}

function handleEdit(row: ProductInfo) {
  editingProduct.value = row
  formVisible.value = true
}

async function handleToggleStatus(row: ProductInfo) {
  const next = row.status === 1 ? 0 : 1
  const action = next === 1 ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(
      `确定要${action}商品「${row.name}」吗？停用后不会出现在入库、出库的可选列表中。`,
      '提示',
      { type: 'warning' },
    )
  } catch {
    return
  }

  await updateProductStatus(row.id, next)
  ElMessage.success(`已${action}`)
  fetchList()
}

async function handleCategoryChanged() {
  await fetchCategories()
  fetchList()
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

      <div v-if="isAdmin" class="toolbar-right">
        <el-button @click="categoryVisible = true">分类管理</el-button>
        <el-button type="primary" @click="handleCreate">新增商品</el-button>
      </div>
    </div>

    <el-table v-loading="loading" :data="rows" border stripe>
      <el-table-column prop="barcode" label="条码" min-width="140" show-overflow-tooltip />
      <el-table-column prop="name" label="商品名称" min-width="180" show-overflow-tooltip />
      <el-table-column label="分类" width="110">
        <template #default="{ row }">{{ row.category_name || '-' }}</template>
      </el-table-column>
      <el-table-column label="规格" width="130" show-overflow-tooltip>
        <template #default="{ row }">{{ row.spec || '-' }}</template>
      </el-table-column>
      <el-table-column label="单位" width="70" align="center">
        <template #default="{ row }">{{ row.unit || '-' }}</template>
      </el-table-column>
      <el-table-column v-if="isAdmin" label="进价" width="100" align="right">
        <template #default="{ row }">{{ formatQty(row.purchase_price) }}</template>
      </el-table-column>
      <el-table-column label="售价" width="100" align="right">
        <template #default="{ row }">{{ formatQty(row.sale_price) }}</template>
      </el-table-column>
      <el-table-column label="安全库存" width="100" align="right">
        <template #default="{ row }">{{ formatQty(row.safe_stock) }}</template>
      </el-table-column>
      <el-table-column label="保质期" width="90" align="center">
        <template #default="{ row }">{{ row.shelf_life_days }} 天</template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
            {{ row.status === 1 ? '正常' : '已停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="isAdmin" label="操作" width="130" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button
            link
            :type="row.status === 1 ? 'danger' : 'success'"
            @click="handleToggleStatus(row)"
          >
            {{ row.status === 1 ? '停用' : '启用' }}
          </el-button>
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

    <ProductFormDialog
      v-model="formVisible"
      :product="editingProduct"
      :categories="activeCategories"
      @success="fetchList"
    />

    <CategoryManageDialog
      v-model="categoryVisible"
      @change="handleCategoryChanged"
    />
  </div>
</template>

<style scoped>
.toolbar-right {
  display: flex;
  gap: 10px;
}
</style>
