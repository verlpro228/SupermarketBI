import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { fetchProfile, login as loginApi } from '@/api/auth'
import { ROLE, TOKEN_KEY, USER_KEY } from '@/constants'
import type { UserInfo } from '@/types'

function readStoredUser(): UserInfo | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as UserInfo
  } catch {
    return null
  }
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) ?? '')
  const user = ref<UserInfo | null>(readStoredUser())

  const isLogin = computed(() => Boolean(token.value))
  const isAdmin = computed(() => user.value?.role === ROLE.ADMIN)
  const displayName = computed(() => user.value?.real_name || user.value?.username || '')

  function setAuth(accessToken: string, userInfo: UserInfo) {
    token.value = accessToken
    user.value = userInfo
    localStorage.setItem(TOKEN_KEY, accessToken)
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
  }

  async function login(username: string, password: string) {
    const { data } = await loginApi({ username, password })
    setAuth(data.access_token, data.user)
    return data
  }

  async function loadProfile() {
    if (!token.value) return null
    const { data } = await fetchProfile()
    user.value = data
    localStorage.setItem(USER_KEY, JSON.stringify(data))
    return data
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return {
    token,
    user,
    isLogin,
    isAdmin,
    displayName,
    login,
    loadProfile,
    logout,
    setAuth,
  }
})
