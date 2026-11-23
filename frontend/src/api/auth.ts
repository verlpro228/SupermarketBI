import type { LoginPayload, LoginResult, UserInfo } from '@/types'

import { request } from './request'

export function login(payload: LoginPayload) {
  return request<LoginResult>({ url: '/auth/login', method: 'post', data: payload })
}

export function fetchProfile() {
  return request<UserInfo>({ url: '/auth/profile', method: 'get' })
}

export function changeMyPassword(payload: { old_password: string; new_password: string }) {
  return request<null>({ url: '/auth/password', method: 'put', data: payload })
}
