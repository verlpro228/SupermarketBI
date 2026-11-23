import { downloadBlob } from '@/utils/download'

import { requestBlob } from './request'

export type ExportType = 'stock' | 'inbound' | 'outbound' | 'expiry' | 'expiry-actions'

/** 请求导出接口并直接触发浏览器下载 */
export async function downloadExport(
  type: ExportType,
  params: Record<string, unknown>,
  fallbackName: string,
): Promise<void> {
  const { blob, filename } = await requestBlob(
    { url: `/export/${type}`, method: 'get', params },
    fallbackName,
  )
  downloadBlob(blob, filename)
}
