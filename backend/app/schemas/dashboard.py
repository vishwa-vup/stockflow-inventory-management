from typing import List, Optional
from pydantic import BaseModel

class DashboardStatsResponse(BaseModel):
    total_products: int
    total_stock: int
    low_stock_count: int
    out_of_stock_count: int
    total_inventory_value: float
    total_suppliers: int

class StockOverviewItem(BaseModel):
    product_code: str
    product_name: str
    current_stock: int
    minimum_stock: int
    maximum_stock: int

class StockMovementItem(BaseModel):
    date: str
    stock_in: int
    stock_out: int

class CategoryDistributionItem(BaseModel):
    category_id: int
    category_name: str
    product_count: int
    inventory_value: float

class LowStockAlertItem(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    current_stock: int
    minimum_stock: int
    maximum_stock: int
    supplier_name: Optional[str] = None
    suggested_reorder: int
    status: str

class ReorderRecommendationItem(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    current_stock: int
    minimum_stock: int
    maximum_stock: int
    suggested_order_quantity: int
    supplier_name: Optional[str] = None
