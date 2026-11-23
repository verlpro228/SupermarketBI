import type { PageResult, ProductInfo, ProductListQuery, ProductOption, ProductPayload } from '@/types'

import { request } from './request'

export function listProducts(params: ProductListQuery) {
  return request<PageResult<ProductInfo>>({ url: '/products', method: 'get', params })
}

export function listProductOptions(keyword?: string) {
  return request<ProductOption[]>({
    url: '/products/options',
    method: 'get',
    params: keyword ? { keyword } : undefined,
  })
}

export function createProduct(data: ProductPayload) {
  return request<ProductInfo>({ url: '/products', method: 'post', data })
}

export function updateProduct(id: number, data: Partial<ProductPayload>) {
  return request<ProductInfo>({ url: `/products/${id}`, method: 'put', data })
}

export function updateProductStatus(id: number, status: number) {
  return request<ProductInfo>({
    url: `/products/${id}/status`,
    method: 'put',
    params: { status },
  })
}
