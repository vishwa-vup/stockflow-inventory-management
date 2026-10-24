from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class InventoryReportItem(BaseModel):
    id: int
    product_code: str
    product_name: str
    category_name: str
    supplier_name: str
    current_stock: int
    purchase_price: float
    selling_price: float
    inventory_value: float
    status: str

class StockMovementReportItem(BaseModel):
    id: int
    date: datetime
    product_code: str
    product_name: str
    type: str
    quantity: int
    user_name: Optional[str] = None
    reference_number: Optional[str] = None
    unit_price: Optional[float] = None

class LowStockReportItem(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    current_stock: int
    minimum_stock: int
    maximum_stock: int
    supplier_name: str
    suggested_reorder_quantity: int
    status: str

class SupplierReportItem(BaseModel):
    supplier_id: int
    supplier_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    products_count: int
    total_stock_quantity: int
    total_inventory_value: float
