import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401  确保全部模型注册到 ORM 元数据
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.response import success
from app.routers.v1.router import api_router

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="超市库存管理日常业务数据分析及可视化系统",
        docs_url="/docs",
        redoc_url=None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(application)
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @application.get("/", include_in_schema=False)
    def root():
        return success({"app": settings.APP_NAME, "docs": "/docs"})

    return application


app = create_app()
