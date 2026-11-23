import type { InspectionDetail, InspectionRecord, PageResult } from '@/types'

import { request } from './request'

export function runInspection() {
  return request<InspectionDetail>({ url: '/inspections/run', method: 'post' })
}

export function listInspections(params: { page: number; page_size: number }) {
  return request<PageResult<InspectionRecord>>({ url: '/inspections', method: 'get', params })
}

export function getInspection(recordId: number) {
  return request<InspectionDetail>({ url: `/inspections/${recordId}`, method: 'get' })
}

export function updateInspectionItems(ids: number[], status: 'handled' | 'ignored') {
  return request<{ count: number }>({
    url: '/inspections/items/status',
    method: 'put',
    data: { ids, status },
  })
}
