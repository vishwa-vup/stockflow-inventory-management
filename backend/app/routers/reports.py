from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.report import (
    InventoryReportItem, StockMovementReportItem, LowStockReportItem, SupplierReportItem
)
from app.services.report_service import (
    generate_inventory_report, generate_stock_movement_report,
    generate_low_stock_report, generate_supplier_report
)
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/inventory", response_model=List[InventoryReportItem])
def get_inventory_report(
    category_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return generate_inventory_report(db, category_id, supplier_id, status)

@router.get("/stock-movement", response_model=List[StockMovementReportItem])
def get_stock_movement_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    transaction_type: Optional[str] = Query(None),
    product_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return generate_stock_movement_report(db, start_date, end_date, transaction_type, product_id)

@router.get("/low-stock", response_model=List[LowStockReportItem])
def get_low_stock_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return generate_low_stock_report(db)

@router.get("/suppliers", response_model=List[SupplierReportItem])
def get_supplier_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return generate_supplier_report(db)
