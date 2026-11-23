import type { CategoryInfo, CategoryOption } from '@/types'

import { request } from './request'

export function listCategories(params?: { status?: number }) {
  return request<CategoryInfo[]>({ url: '/categories', method: 'get', params })
}

export function listCategoryOptions() {
  return request<CategoryOption[]>({ url: '/categories/options', method: 'get' })
}

export function createCategory(data: { name: string; sort_order?: number }) {
  return request<CategoryInfo>({ url: '/categories', method: 'post', data })
}

export function updateCategory(id: number, data: { name?: string; sort_order?: number }) {
  return request<CategoryInfo>({ url: `/categories/${id}`, method: 'put', data })
}

export function updateCategoryStatus(id: number, status: number) {
  return request<CategoryInfo>({
    url: `/categories/${id}/status`,
    method: 'put',
    params: { status },
  })
}
