from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class StockInRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    supplier_id: Optional[int] = Field(None, gt=0)
    quantity: int = Field(..., gt=0, description="Quantity must be greater than zero")
    unit_purchase_price: Optional[float] = Field(None, ge=0.0)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    date: Optional[datetime] = None

class StockOutRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, description="Quantity must be greater than zero")
    customer_department: Optional[str] = Field(None, max_length=100)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    date: Optional[datetime] = None

class TransactionResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_code: str
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    transaction_type: str  # 'STOCK_IN' or 'STOCK_OUT'
    quantity: int
    previous_stock: int
    new_stock: int
    unit_price: Optional[float] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    limit: int
    total_pages: int
