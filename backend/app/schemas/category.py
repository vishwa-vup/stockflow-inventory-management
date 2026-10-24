from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    product_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
