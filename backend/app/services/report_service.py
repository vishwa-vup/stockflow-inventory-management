from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.transaction import Transaction
from app.schemas.report import (
    InventoryReportItem, StockMovementReportItem, LowStockReportItem, SupplierReportItem
)

def get_product_status(current_stock: int, minimum_stock: int) -> str:
    if current_stock == 0:
        return "OUT_OF_STOCK"
    elif current_stock <= minimum_stock:
        return "LOW_STOCK"
    return "IN_STOCK"

def generate_inventory_report(
    db: Session,
    category_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    status_filter: Optional[str] = None
) -> List[InventoryReportItem]:
    query = db.query(Product)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if supplier_id:
        query = query.filter(Product.supplier_id == supplier_id)

    products = query.all()
    results = []
    for p in products:
        stat = get_product_status(p.current_stock, p.minimum_stock)
        if status_filter and stat != status_filter:
            continue
        results.append(
            InventoryReportItem(
                id=p.id,
                product_code=p.product_code,
                product_name=p.name,
                category_name=p.category.name if p.category else "Unassigned",
                supplier_name=p.supplier.name if p.supplier else "Unassigned",
                current_stock=p.current_stock,
                purchase_price=round(p.purchase_price, 2),
                selling_price=round(p.selling_price, 2),
                inventory_value=round(p.current_stock * p.purchase_price, 2),
                status=stat
            )
        )
    return results

def generate_stock_movement_report(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    transaction_type: Optional[str] = None,
    product_id: Optional[int] = None
) -> List[StockMovementReportItem]:
    query = db.query(Transaction)
    if start_date:
        query = query.filter(Transaction.created_at >= start_date)
    if end_date:
        query = query.filter(Transaction.created_at <= end_date)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if product_id:
        query = query.filter(Transaction.product_id == product_id)

    transactions = query.order_by(Transaction.created_at.desc()).all()
    results = []
    for tx in transactions:
        results.append(
            StockMovementReportItem(
                id=tx.id,
                date=tx.created_at,
                product_code=tx.product.product_code if tx.product else "N/A",
                product_name=tx.product.name if tx.product else "N/A",
                type=tx.transaction_type,
                quantity=tx.quantity,
                user_name=tx.user.name if tx.user else "System",
                reference_number=tx.reference_number,
                unit_price=tx.unit_price
            )
        )
    return results

def generate_low_stock_report(db: Session) -> List[LowStockReportItem]:
    products = db.query(Product).filter(Product.current_stock <= Product.minimum_stock).all()
    results = []
    for p in products:
        suggested = max(0, p.maximum_stock - p.current_stock)
        stat = "OUT_OF_STOCK" if p.current_stock == 0 else "LOW_STOCK"
        results.append(
            LowStockReportItem(
                product_id=p.id,
                product_code=p.product_code,
                product_name=p.name,
                current_stock=p.current_stock,
                minimum_stock=p.minimum_stock,
                maximum_stock=p.maximum_stock,
                supplier_name=p.supplier.name if p.supplier else "N/A",
                suggested_reorder_quantity=suggested,
                status=stat
            )
        )
    return results

def generate_supplier_report(db: Session) -> List[SupplierReportItem]:
    suppliers = db.query(Supplier).all()
    results = []
    for s in suppliers:
        prods = s.products
        count = len(prods)
        stock_qty = sum(p.current_stock for p in prods)
        inv_val = sum(p.current_stock * p.purchase_price for p in prods)
        results.append(
            SupplierReportItem(
                supplier_id=s.id,
                supplier_name=s.name,
                contact_person=s.contact_person,
                phone=s.phone,
                email=s.email,
                products_count=count,
                total_stock_quantity=stock_qty,
                total_inventory_value=round(inv_val, 2)
            )
        )
    return results
