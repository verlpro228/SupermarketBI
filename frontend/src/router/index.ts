import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { APP_TITLE, TOKEN_KEY, USER_KEY } from '@/constants'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/',
    component: () => import('@/layouts/BasicLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '数据看板', icon: 'DataBoard' },
      },
      {
        path: 'inbound',
        name: 'Inbound',
        component: () => import('@/views/inbound/index.vue'),
        meta: { title: '入库登记', icon: 'Download' },
      },
      {
        path: 'outbound',
        name: 'Outbound',
        component: () => import('@/views/outbound/index.vue'),
        meta: { title: '出库登记', icon: 'Upload' },
      },
      {
        path: 'stock',
        name: 'Stock',
        component: () => import('@/views/stock/index.vue'),
        meta: { title: '库存查询', icon: 'Box' },
      },
      {
        path: 'expiry',
        name: 'Expiry',
        component: () => import('@/views/expiry/index.vue'),
        meta: { title: '临期清单', icon: 'AlarmClock' },
      },
      {
        path: 'inspection',
        name: 'Inspection',
        component: () => import('@/views/inspection/index.vue'),
        meta: { title: '库存巡检', icon: 'Search' },
      },
      {
        path: 'trend',
        name: 'Trend',
        component: () => import('@/views/trend/index.vue'),
        meta: { title: '出入库趋势', icon: 'TrendCharts' },
      },
      {
        path: 'product',
        name: 'Product',
        component: () => import('@/views/product/index.vue'),
        meta: { title: '商品管理', icon: 'Goods' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/user/index.vue'),
        meta: { title: '用户管理', icon: 'User', roles: ['admin'] },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: { public: true, title: '页面不存在' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function readRole(): string {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return ''
  try {
    return (JSON.parse(raw) as { role?: string }).role ?? ''
  } catch {
    return ''
  }
}

router.beforeEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - ${APP_TITLE}` : APP_TITLE

  const hasToken = Boolean(localStorage.getItem(TOKEN_KEY))

  if (to.meta.public) {
    if (to.path === '/login' && hasToken) {
      return { path: '/' }
    }
    return true
  }

  if (!hasToken) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  const roles = to.meta.roles as string[] | undefined
  if (roles && roles.length > 0 && !roles.includes(readRole())) {
    return { path: '/dashboard' }
  }

  return true
})

export default router
