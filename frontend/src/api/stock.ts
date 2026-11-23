import type {
  PageResult,
  StockAdjustPayload,
  StockBatch,
  StockInfo,
  StockQuery,
  StockRecord,
} from '@/types'

import { request } from './request'

export function listStock(params: StockQuery) {
  return request<PageResult<StockInfo>>({ url: '/stock', method: 'get', params })
}

export function listStockRecords(productId: number, params: { page: number; page_size: number }) {
  return request<PageResult<StockRecord>>({
    url: `/stock/${productId}/records`,
    method: 'get',
    params,
  })
}

export function listStockBatches(productId: number) {
  return request<StockBatch[]>({ url: `/stock/${productId}/batches`, method: 'get' })
}

export function adjustStock(data: StockAdjustPayload) {
  return request<null>({ url: '/stock/adjust', method: 'post', data })
}
