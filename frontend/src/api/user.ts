import type {
  PageResult,
  UserCreatePayload,
  UserInfo,
  UserListQuery,
  UserUpdatePayload,
} from '@/types'

import { request } from './request'

export function listUsers(params: UserListQuery) {
  return request<PageResult<UserInfo>>({ url: '/users', method: 'get', params })
}

export function createUser(data: UserCreatePayload) {
  return request<UserInfo>({ url: '/users', method: 'post', data })
}

export function updateUser(id: number, data: UserUpdatePayload) {
  return request<UserInfo>({ url: `/users/${id}`, method: 'put', data })
}

export function updateUserStatus(id: number, status: number) {
  return request<UserInfo>({ url: `/users/${id}/status`, method: 'put', data: { status } })
}

export function resetUserPassword(id: number, newPassword: string) {
  return request<null>({
    url: `/users/${id}/password`,
    method: 'put',
    data: { new_password: newPassword },
  })
}
