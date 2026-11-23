import type { InboundCreatePayload, InboundInfo, InboundQuery, PageResult } from '@/types'

import { request } from './request'

export function createInbound(data: InboundCreatePayload) {
  return request<InboundInfo>({ url: '/inbound', method: 'post', data })
}

export function listInbounds(params: InboundQuery) {
  return request<PageResult<InboundInfo>>({ url: '/inbound', method: 'get', params })
}
