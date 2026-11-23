import axios, { type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

import { TOKEN_KEY, USER_KEY } from '@/constants'
import type { ApiResult } from '@/types'
import { resolveFilename } from '@/utils/download'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 20000,
})

service.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

service.interceptors.response.use(
  (response) => {
    const body = response.data as ApiResult | Blob
    if (body instanceof Blob) {
      return response
    }
    if (body && typeof body.code === 'number' && body.code !== 0) {
      ElMessage.error(body.message || '操作失败')
      return Promise.reject(new Error(body.message))
    }
    return response
  },
  (error) => {
    const status: number | undefined = error.response?.status
    const message: string =
      error.response?.data?.message ?? error.message ?? '网络异常，请稍后重试'

    if (status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    ElMessage.error(message)
    return Promise.reject(error)
  },
)

/** 普通接口请求 */
export async function request<T>(config: AxiosRequestConfig): Promise<ApiResult<T>> {
  const response = await service.request<ApiResult<T>>(config)
  return response.data
}

/** 文件下载请求，返回 Blob 与解析后的文件名 */
export async function requestBlob(
  config: AxiosRequestConfig,
  fallbackName: string,
): Promise<{ blob: Blob; filename: string }> {
  const response: AxiosResponse<Blob> = await service.request<Blob>({
    ...config,
    responseType: 'blob',
  })
  return {
    blob: response.data,
    filename: resolveFilename(
      response.headers['content-disposition'] as string | undefined,
      fallbackName,
    ),
  }
}

export default service
