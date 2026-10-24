from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class SupplierBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    gst_number: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    gst_number: Optional[str] = None

class SupplierResponse(SupplierBase):
    id: int
    product_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
