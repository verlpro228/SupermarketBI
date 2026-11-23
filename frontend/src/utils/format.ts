import dayjs from 'dayjs'

type NumberLike = number | string | null | undefined

/** 金额格式化：1,234.56 */
export function formatMoney(value: NumberLike, digits = 2): string {
  const num = Number(value ?? 0)
  if (Number.isNaN(num)) return '-'
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

/** 数量格式化：保留 3 位小数并去掉多余的 0 */
export function formatQty(value: NumberLike): string {
  const num = Number(value ?? 0)
  if (Number.isNaN(num)) return '-'
  return String(Number(num.toFixed(3)))
}

/** 日期格式化 */
export function formatDate(value?: string | null): string {
  if (!value) return '-'
  const d = dayjs(value)
  return d.isValid() ? d.format('YYYY-MM-DD') : '-'
}

/** 日期时间格式化 */
export function formatDateTime(value?: string | null): string {
  if (!value) return '-'
  const d = dayjs(value)
  return d.isValid() ? d.format('YYYY-MM-DD HH:mm:ss') : '-'
}

/** 剩余天数展示 */
export function formatDaysLeft(days?: number | null): string {
  if (days === null || days === undefined) return '-'
  if (days < 0) return `已过期 ${Math.abs(days)} 天`
  return `${days} 天`
}
