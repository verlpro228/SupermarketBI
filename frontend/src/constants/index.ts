/** 系统名称：与课题名保持一致 */
export const APP_TITLE = '超市库存管理日常业务数据分析及可视化系统'
export const APP_NAME_SHORT = '超市库存管理'
export const APP_SUBTITLE = '日常业务数据分析及可视化系统'

/** 本地存储键名 */
export const TOKEN_KEY = 'sbi_token'
export const USER_KEY = 'sbi_user'

/** 角色枚举 */
export const ROLE = {
  ADMIN: 'admin',
  KEEPER: 'keeper',
} as const

export const ROLE_LABEL: Record<string, string> = {
  admin: '管理员',
  keeper: '库管员',
}

/** 出库类型 */
export const OUTBOUND_TYPE = {
  SALE: 'sale',
  LOSS: 'loss',
} as const

export const OUTBOUND_TYPE_LABEL: Record<string, string> = {
  sale: '销售出库',
  loss: '报损出库',
}

/** 临期分档 */
export const EXPIRY_LEVEL = {
  EXPIRED: 'expired',
  URGENT: 'urgent',
  WARNING: 'warning',
  NORMAL: 'normal',
} as const

export const EXPIRY_LEVEL_LABEL: Record<string, string> = {
  expired: '已过期',
  urgent: '紧急',
  warning: '预警',
  normal: '正常',
}

/** 巡检问题状态 */
export const INSPECTION_STATUS_LABEL: Record<string, string> = {
  pending: '待处理',
  handled: '已处理',
  ignored: '已忽略',
}
