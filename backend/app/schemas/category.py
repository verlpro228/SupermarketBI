from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    sort_order: int = Field(0, ge=0, le=9999, description="排序号")


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50, description="分类名称")
    sort_order: int | None = Field(None, ge=0, le=9999, description="排序号")


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sort_order: int
    status: int


class CategoryOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
