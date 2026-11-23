from fastapi import APIRouter

from app.routers.v1 import (
    auth,
    category,
    expiry,
    export,
    inbound,
    inspection,
    outbound,
    product,
    stats,
    stock,
    system,
    user,
)

api_router = APIRouter()

# 系统
api_router.include_router(system.router, prefix="/system", tags=["系统"])
# 认证
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
# 用户管理
api_router.include_router(user.router, prefix="/users", tags=["用户管理"])
# 基础档案
api_router.include_router(category.router, prefix="/categories", tags=["商品分类"])
api_router.include_router(product.router, prefix="/products", tags=["商品管理"])
# 出入库
api_router.include_router(inbound.router, prefix="/inbound", tags=["入库"])
api_router.include_router(outbound.router, prefix="/outbound", tags=["出库"])
api_router.include_router(stock.router, prefix="/stock", tags=["库存"])
# 临期与巡检
api_router.include_router(expiry.router, prefix="/expiry", tags=["临期"])
api_router.include_router(inspection.router, prefix="/inspections", tags=["巡检"])
# 统计与导出
api_router.include_router(stats.router, prefix="/stats", tags=["统计分析"])
api_router.include_router(export.router, prefix="/export", tags=["数据导出"])
