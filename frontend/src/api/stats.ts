import type {
  DashboardData,
  InboundAnalysis,
  OutboundAnalysis,
  TrendGranularity,
  TrendPoint,
} from '@/types'

import { request } from './request'

export function getDashboard(days = 30) {
  return request<DashboardData>({ url: '/stats/dashboard', method: 'get', params: { days } })
}

export function getTrend(params: { days: number; granularity: TrendGranularity }) {
  return request<{ granularity: TrendGranularity; days: number; items: TrendPoint[] }>({
    url: '/stats/trend',
    method: 'get',
    params,
  })
}

export function getInboundAnalysis(days = 30) {
  return request<InboundAnalysis>({
    url: '/stats/inbound-analysis',
    method: 'get',
    params: { days },
  })
}

export function getOutboundAnalysis(days = 30) {
  return request<OutboundAnalysis>({
    url: '/stats/outbound-analysis',
    method: 'get',
    params: { days },
  })
}
