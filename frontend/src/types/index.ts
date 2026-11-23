export type UserRole = 'admin' | 'keeper'

export interface UserInfo {
  id: number
  username: string
  real_name: string | null
  role: UserRole
  status: number
  last_login_at: string | null
  created_at?: string | null
}

export interface UserListQuery extends PageQuery {
  keyword?: string
  role?: UserRole
  status?: number
}

export interface UserCreatePayload {
  username: string
  password: string
  real_name?: string | null
  role: UserRole
}

export interface UserUpdatePayload {
  real_name?: string | null
  role?: UserRole
}

export interface LoginPayload {
  username: string
  password: string
}

export interface LoginResult {
  access_token: string
  token_type: string
  user: UserInfo
}

/** 后端统一响应体 */
export interface ApiResult<T = unknown> {
  code: number
  message: string
  data: T
}

/** 分页请求参数 */
export interface PageQuery {
  page: number
  page_size: number
}

/** 分页响应数据 */
export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** 商品分类 */
export interface CategoryInfo {
  id: number
  name: string
  sort_order: number
  status: number
}

export interface CategoryOption {
  id: number
  name: string
}

/** 商品档案 */
export interface ProductInfo {
  id: number
  barcode: string
  name: string
  category_id: number
  category_name: string | null
  spec: string | null
  unit: string | null
  purchase_price?: number
  sale_price: number
  safe_stock: number
  shelf_life_days: number
  status: number
  created_at?: string | null
}

export interface ProductListQuery extends PageQuery {
  keyword?: string
  category_id?: number
  status?: number
}

export interface ProductPayload {
  barcode: string
  name: string
  category_id: number
  spec?: string | null
  unit?: string | null
  purchase_price: number
  sale_price: number
  safe_stock: number
  shelf_life_days: number
}

export interface ProductOption {
  id: number
  barcode: string
  name: string
  spec: string | null
  unit: string | null
  shelf_life_days: number
  stock_qty: number
  purchase_price: number | null
}

/** 入库记录 */
export interface InboundInfo {
  id: number
  order_no: string
  product_id: number
  product_name: string | null
  barcode: string | null
  unit: string | null
  batch_no: string | null
  quantity: number
  cost_price: number
  amount: number
  production_date: string
  expiry_date: string
  supplier: string | null
  operator_name: string | null
  remark: string | null
  created_at: string | null
}

export interface InboundQuery extends PageQuery {
  keyword?: string
  product_id?: number
  start_date?: string
  end_date?: string
}

export interface InboundCreatePayload {
  product_id: number
  quantity: number
  cost_price: number
  production_date: string
  supplier?: string | null
  remark?: string | null
}

/** 库存 */
export interface StockInfo {
  product_id: number
  barcode: string
  name: string
  category_id: number
  category_name: string | null
  unit: string | null
  total_qty: number
  safe_stock: number
  nearest_expiry: string | null
  days_left: number | null
  product_status: number
  is_low_stock: boolean
  purchase_price?: number
  stock_value?: number
}

export interface StockQuery extends PageQuery {
  keyword?: string
  category_id?: number
  status?: number
}

export interface StockRecord {
  record_type: 'inbound' | 'outbound'
  order_no: string
  batch_no: string | null
  quantity: number
  amount: number
  production_date: string | null
  expiry_date: string | null
  days_left: number | null
  supplier: string | null
  outbound_type: string | null
  reason: string | null
  operator_name: string | null
  created_at: string | null
}

export interface StockBatch {
  batch_id: number
  batch_no: string
  production_date: string
  expiry_date: string
  qty_remaining: number
  cost_price: number
  days_left: number
}

export interface StockAdjustPayload {
  product_id: number
  batch_id: number
  new_qty: number
  reason: string
}

/** 出库 */
export type OutboundType = 'sale' | 'loss'

export interface OutboundItemInfo {
  batch_id: number
  batch_no: string | null
  quantity: number
  cost_price: number
  amount: number
  production_date: string | null
  expiry_date: string | null
}

export interface OutboundInfo {
  id: number
  order_no: string
  product_id: number | null
  product_name: string | null
  barcode: string | null
  unit: string | null
  outbound_type: OutboundType
  total_qty: number
  total_amount: number
  reason: string | null
  operator_name: string | null
  remark: string | null
  created_at: string | null
  items: OutboundItemInfo[]
}

export interface OutboundQuery extends PageQuery {
  keyword?: string
  outbound_type?: OutboundType
  start_date?: string
  end_date?: string
}

export interface OutboundCreatePayload {
  product_id: number
  outbound_type: OutboundType
  quantity: number
  reason?: string | null
  remark?: string | null
}

/** 临期 */
export type ExpiryLevel = 'expired' | 'urgent' | 'warning' | 'normal'

export interface ExpiryBatch {
  batch_id: number
  batch_no: string
  product_id: number
  product_name: string
  barcode: string
  unit: string | null
  category_id: number | null
  category_name: string | null
  production_date: string
  expiry_date: string
  days_left: number
  qty_remaining: number
  level: ExpiryLevel
  is_promo: number
  cost_price?: number
  stock_value?: number
}

export interface ExpiryQuery extends PageQuery {
  level?: ExpiryLevel
  category_id?: number
  keyword?: string
}

export interface ExpiryThresholds {
  urgent_days: number
  warning_days: number
}

export interface ExpiryPageResult extends PageResult<ExpiryBatch> {
  thresholds: ExpiryThresholds
}

export interface ExpiryActionLog {
  id: number
  product_id: number
  product_name: string | null
  barcode: string | null
  batch_id: number
  batch_no: string | null
  action: 'loss' | 'promo'
  quantity: number
  order_no: string | null
  operator_name: string | null
  created_at: string | null
}

export interface ExpiryActionQuery extends PageQuery {
  keyword?: string
  action?: 'loss' | 'promo'
}

/** 巡检 */
export interface InspectionItem {
  id: number
  product_id: number
  product_name: string | null
  barcode: string | null
  unit: string | null
  batch_id: number | null
  batch_no: string | null
  problem_type: 'low_stock' | 'near_expiry'
  gap_qty: number | null
  days_left: number | null
  status: 'pending' | 'handled' | 'ignored'
  handled_at: string | null
}

export interface InspectionRecord {
  id: number
  inspector_name: string | null
  hit_count: number
  low_stock_count: number
  near_expiry_count: number
  pending_count: number
  created_at: string | null
}

export interface InspectionDetail extends InspectionRecord {
  items: InspectionItem[]
}

/** 统计 */
export interface DashboardKpi {
  product_count: number
  total_stock: number
  stock_value: number | null
  expiry_count: number
}

export interface TrendPoint {
  label: string
  inbound: number
  outbound: number
}

export interface CategoryValue {
  category: string
  value: number
}

export interface CategoryFlowItem {
  category: string
  inbound: number
  outbound: number
}

export interface ExpiryLevelCount {
  level: ExpiryLevel
  count: number
}

export interface ProductValueItem {
  name: string
  value: number
}

export interface LowStockItem {
  name: string
  gap: number
}

export interface DashboardData {
  kpi: DashboardKpi
  trend: TrendPoint[]
  category_value: CategoryValue[]
  category_flow: CategoryFlowItem[]
  expiry_distribution: ExpiryLevelCount[]
  top_value_products: ProductValueItem[]
  low_stock_products: LowStockItem[]
}

export type TrendGranularity = 'day' | 'month'

/** 出入库分析 */
export interface IoTrendItem {
  label: string
  quantity: number
  orders: number
}

export interface SupplierRankItem {
  supplier: string
  quantity: number
  orders: number
}

export interface CategoryQuantityItem {
  category: string
  quantity: number
}

export interface OutboundTypeItem {
  type: OutboundType
  quantity: number
  orders: number
}

export interface ProductQuantityItem {
  name: string
  quantity: number
}

export interface InboundAnalysis {
  days: number
  trend: IoTrendItem[]
  supplier_ranking: SupplierRankItem[]
  category_distribution: CategoryQuantityItem[]
}

export interface OutboundAnalysis {
  days: number
  trend: IoTrendItem[]
  type_distribution: OutboundTypeItem[]
  top_products: ProductQuantityItem[]
}
