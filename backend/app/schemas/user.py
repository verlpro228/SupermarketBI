from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.schemas.base import PageQuery

UserRole = Literal["admin", "keeper"]


class LoginPayload(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="账号")
    password: str = Field(..., min_length=1, max_length=72, description="密码")


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    real_name: str | None = None
    role: str
    status: int
    last_login_at: datetime | None = None
    created_at: datetime | None = None

    @field_serializer("last_login_at", "created_at")
    def _serialize_datetime(self, value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserQuery(PageQuery):
    keyword: str | None = Field(None, max_length=50, description="账号或姓名模糊搜索")
    role: UserRole | None = Field(None, description="角色筛选")
    status: int | None = Field(None, ge=0, le=1, description="状态筛选")


class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
        description="账号，字母开头，可含数字和下划线",
    )
    password: str = Field(..., min_length=6, max_length=72, description="初始密码")
    real_name: str | None = Field(None, max_length=50, description="姓名")
    role: UserRole = Field("keeper", description="角色")


class UserUpdate(BaseModel):
    real_name: str | None = Field(None, max_length=50, description="姓名")
    role: UserRole | None = Field(None, description="角色")


class UserStatusPayload(BaseModel):
    status: int = Field(..., ge=0, le=1, description="1 启用 0 禁用")


class ResetPasswordPayload(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=72, description="新密码")


class ChangePasswordPayload(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=72, description="原密码")
    new_password: str = Field(..., min_length=6, max_length=72, description="新密码")
