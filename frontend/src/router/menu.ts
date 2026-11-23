import type { UserRole } from '@/types'

export interface MenuItem {
  path: string
  title: string
  icon: string
  roles?: UserRole[]
}

export interface MenuGroup {
  title?: string
  items: MenuItem[]
}

/** 侧边导航配置，roles 为空表示所有角色可见 */
export const MENU_GROUPS: MenuGroup[] = [
  {
    items: [{ path: '/dashboard', title: '数据看板', icon: 'DataBoard' }],
  },
  {
    title: '出入库',
    items: [
      { path: '/inbound', title: '入库登记', icon: 'Download' },
      { path: '/outbound', title: '出库登记', icon: 'Upload' },
      { path: '/stock', title: '库存查询', icon: 'Box' },
    ],
  },
  {
    title: '临期与巡检',
    items: [
      { path: '/expiry', title: '临期清单', icon: 'AlarmClock' },
      { path: '/inspection', title: '库存巡检', icon: 'Search' },
    ],
  },
  {
    title: '统计分析',
    items: [{ path: '/trend', title: '出入库趋势', icon: 'TrendCharts' }],
  },
  {
    title: '基础档案',
    items: [
      { path: '/product', title: '商品管理', icon: 'Goods' },
      { path: '/users', title: '用户管理', icon: 'User', roles: ['admin'] },
    ],
  },
]

/** 按角色过滤菜单，过滤后为空的分组自动隐藏 */
export function filterMenuGroups(role: string): MenuGroup[] {
  return MENU_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => !item.roles || item.roles.includes(role as UserRole)),
  })).filter((group) => group.items.length > 0)
}
