import type {
  OutboundCreatePayload,
  OutboundInfo,
  OutboundQuery,
  PageResult,
} from '@/types'

import { request } from './request'

export function createOutbound(data: OutboundCreatePayload) {
  return request<OutboundInfo>({ url: '/outbound', method: 'post', data })
}

export function listOutbounds(params: OutboundQuery) {
  return request<PageResult<OutboundInfo>>({ url: '/outbound', method: 'get', params })
}
