from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator

class ProductBase(BaseModel):
    product_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    category_id: int = Field(..., gt=0)
    supplier_id: int = Field(..., gt=0)
    purchase_price: float = Field(..., ge=0.0, description="Purchase price cannot be negative")
    selling_price: float = Field(..., ge=0.0, description="Selling price cannot be negative")
    minimum_stock: int = Field(5, ge=0, description="Minimum stock cannot be negative")
    maximum_stock: int = Field(100, ge=1, description="Maximum stock must be at least 1")
    location: Optional[str] = None

    @model_validator(mode="after")
    def validate_min_max(self):
        if self.maximum_stock <= self.minimum_stock:
            raise ValueError("Maximum stock must be strictly greater than minimum stock")
        return self

class ProductCreate(ProductBase):
    initial_stock: int = Field(0, ge=0, description="Stock cannot be negative")

class ProductUpdate(BaseModel):
    product_code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = Field(None, gt=0)
    supplier_id: Optional[int] = Field(None, gt=0)
    purchase_price: Optional[float] = Field(None, ge=0.0)
    selling_price: Optional[float] = Field(None, ge=0.0)
    minimum_stock: Optional[int] = Field(None, ge=0)
    maximum_stock: Optional[int] = Field(None, ge=1)
    location: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    product_code: str
    name: str
    description: Optional[str] = None
    category_id: int
    supplier_id: int
    category_name: Optional[str] = None
    supplier_name: Optional[str] = None
    purchase_price: float
    selling_price: float
    current_stock: int
    minimum_stock: int
    maximum_stock: int
    location: Optional[str] = None
    status: str  # 'IN_STOCK', 'LOW_STOCK', 'OUT_OF_STOCK'
    inventory_value: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    limit: int
    total_pages: int
