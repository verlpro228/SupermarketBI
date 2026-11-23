import { request } from './request'

export interface HealthInfo {
  status: string
  app: string
  database: string
}

export function getHealth() {
  return request<HealthInfo>({ url: '/system/health', method: 'get' })
}
