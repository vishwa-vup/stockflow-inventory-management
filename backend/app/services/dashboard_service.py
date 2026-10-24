from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.dashboard import (
    DashboardStatsResponse, StockOverviewItem, StockMovementItem,
    CategoryDistributionItem, LowStockAlertItem, ReorderRecommendationItem
)

def get_dashboard_stats(db: Session) -> DashboardStatsResponse:
    products = db.query(Product).all()
    total_suppliers = db.query(func.count(Supplier.id)).scalar() or 0

    total_products = len(products)
    total_stock = sum(p.current_stock for p in products)
    low_stock_count = sum(1 for p in products if p.current_stock <= p.minimum_stock)
    out_of_stock_count = sum(1 for p in products if p.current_stock == 0)
    total_inventory_value = sum(p.current_stock * p.purchase_price for p in products)

    return DashboardStatsResponse(
        total_products=total_products,
        total_stock=total_stock,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        total_inventory_value=round(total_inventory_value, 2),
        total_suppliers=total_suppliers
    )

def get_stock_overview(db: Session, limit: int = 10) -> List[StockOverviewItem]:
    products = db.query(Product).order_by(Product.current_stock.asc()).limit(limit).all()
    return [
        StockOverviewItem(
            product_code=p.product_code,
            product_name=p.name,
            current_stock=p.current_stock,
            minimum_stock=p.minimum_stock,
            maximum_stock=p.maximum_stock
        )
        for p in products
    ]

def get_stock_movement(db: Session, days: int = 7) -> List[StockMovementItem]:
    start_date = datetime.now(timezone.utc) - timedelta(days=days - 1)
    # Default dict for each date in range
    movement_map: Dict[str, Dict[str, int]] = {}
    for i in range(days):
        d_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        movement_map[d_str] = {"stock_in": 0, "stock_out": 0}

    transactions = db.query(Transaction).filter(Transaction.created_at >= start_date.replace(hour=0, minute=0, second=0)).all()
    for tx in transactions:
        d_str = tx.created_at.strftime("%Y-%m-%d")
        if d_str in movement_map:
            if tx.transaction_type == "STOCK_IN":
                movement_map[d_str]["stock_in"] += tx.quantity
            elif tx.transaction_type == "STOCK_OUT":
                movement_map[d_str]["stock_out"] += tx.quantity

    return [
        StockMovementItem(
            date=d,
            stock_in=movement_map[d]["stock_in"],
            stock_out=movement_map[d]["stock_out"]
        )
        for d in sorted(movement_map.keys())
    ]

def get_category_distribution(db: Session) -> List[CategoryDistributionItem]:
    categories = db.query(Category).all()
    results = []
    for cat in categories:
        products = cat.products
        count = len(products)
        val = sum(p.current_stock * p.purchase_price for p in products)
        results.append(
            CategoryDistributionItem(
                category_id=cat.id,
                category_name=cat.name,
                product_count=count,
                inventory_value=round(val, 2)
            )
        )
    return results

def get_low_stock_alerts(db: Session) -> List[LowStockAlertItem]:
    products = db.query(Product).filter(Product.current_stock <= Product.minimum_stock).all()
    items = []
    for p in products:
        suggested = max(0, p.maximum_stock - p.current_stock)
        status_str = "OUT_OF_STOCK" if p.current_stock == 0 else "LOW_STOCK"
        items.append(
            LowStockAlertItem(
                product_id=p.id,
                product_code=p.product_code,
                product_name=p.name,
                current_stock=p.current_stock,
                minimum_stock=p.minimum_stock,
                maximum_stock=p.maximum_stock,
                supplier_name=p.supplier.name if p.supplier else "N/A",
                suggested_reorder=suggested,
                status=status_str
            )
        )
    return sorted(items, key=lambda x: (x.current_stock, x.product_name))

def get_reorder_recommendations(db: Session) -> List[ReorderRecommendationItem]:
    products = db.query(Product).filter(Product.current_stock <= Product.minimum_stock).all()
    items = []
    for p in products:
        suggested = max(0, p.maximum_stock - p.current_stock)
        items.append(
            ReorderRecommendationItem(
                product_id=p.id,
                product_code=p.product_code,
                product_name=p.name,
                current_stock=p.current_stock,
                minimum_stock=p.minimum_stock,
                maximum_stock=p.maximum_stock,
                suggested_order_quantity=suggested,
                supplier_name=p.supplier.name if p.supplier else "N/A"
            )
        )
    return sorted(items, key=lambda x: (x.current_stock, x.suggested_order_quantity), reverse=True)
