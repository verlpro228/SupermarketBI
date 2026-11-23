import type {
  ExpiryActionLog,
  ExpiryActionQuery,
  ExpiryPageResult,
  ExpiryQuery,
  PageResult,
} from '@/types'

import { request } from './request'

export function listExpiry(params: ExpiryQuery) {
  return request<ExpiryPageResult>({ url: '/expiry', method: 'get', params })
}

export function createExpiryLoss(data: {
  items: { batch_id: number; quantity: number }[]
  reason: string
}) {
  return request<{ count: number }>({ url: '/expiry/loss', method: 'post', data })
}

export function markExpiryPromo(batchId: number) {
  return request<null>({ url: '/expiry/promo', method: 'post', data: { batch_id: batchId } })
}

export function listExpiryActions(params: ExpiryActionQuery) {
  return request<PageResult<ExpiryActionLog>>({
    url: '/expiry/actions',
    method: 'get',
    params,
  })
}
