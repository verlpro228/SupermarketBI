/** 触发浏览器下载 Blob */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

/** 从 Content-Disposition 响应头解析文件名，兼容 UTF-8 编码 */
export function resolveFilename(disposition: string | undefined, fallback: string): string {
  if (!disposition) return fallback

  const utf8Match = /filename\*=UTF-8''([^;]+)/i.exec(disposition)
  if (utf8Match?.[1]) {
    try {
      return decodeURIComponent(utf8Match[1])
    } catch {
      return fallback
    }
  }

  const plainMatch = /filename="?([^";]+)"?/i.exec(disposition)
  return plainMatch?.[1] ?? fallback
}
