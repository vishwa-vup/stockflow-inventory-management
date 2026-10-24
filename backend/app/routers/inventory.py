import math
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from app.database import get_db
from app.models.transaction import Transaction
from app.models.product import Product
from app.models.user import User
from app.schemas.transaction import (
    StockInRequest, StockOutRequest, TransactionResponse, TransactionListResponse
)
from app.services.inventory_service import process_stock_in, process_stock_out
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/inventory", tags=["Inventory Operations"])

def build_tx_response(tx: Transaction) -> TransactionResponse:
    return TransactionResponse(
        id=tx.id,
        product_id=tx.product_id,
        product_name=tx.product.name if tx.product else "Unknown",
        product_code=tx.product.product_code if tx.product else "N/A",
        user_id=tx.user_id,
        user_name=tx.user.name if tx.user else "System",
        transaction_type=tx.transaction_type,
        quantity=tx.quantity,
        previous_stock=tx.previous_stock,
        new_stock=tx.new_stock,
        unit_price=round(tx.unit_price, 2) if tx.unit_price is not None else None,
        reference_number=tx.reference_number,
        notes=tx.notes,
        created_at=tx.created_at
    )

@router.post("/stock-in", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def stock_in(
    req: StockInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tx = process_stock_in(db, req, current_user)
    return build_tx_response(tx)

@router.post("/stock-out", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def stock_out(
    req: StockOutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tx = process_stock_out(db, req, current_user)
    return build_tx_response(tx)

@router.get("/transactions", response_model=TransactionListResponse)
def get_transactions(
    search: Optional[str] = Query(None, description="Search by product name, code, reference number, or notes"),
    transaction_type: Optional[str] = Query(None, description="STOCK_IN or STOCK_OUT"),
    product_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Transaction).join(Product, Product.id == Transaction.product_id)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(s),
                Product.product_code.ilike(s),
                Transaction.reference_number.ilike(s),
                Transaction.notes.ilike(s)
            )
        )

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type.upper().strip())

    if product_id:
        query = query.filter(Transaction.product_id == product_id)

    if start_date:
        query = query.filter(Transaction.created_at >= start_date)

    if end_date:
        query = query.filter(Transaction.created_at <= end_date)

    total = query.count()
    offset = (page - 1) * limit
    transactions = query.order_by(desc(Transaction.created_at)).offset(offset).limit(limit).all()
    total_pages = math.ceil(total / limit) if limit > 0 else 1

    items = [build_tx_response(t) for t in transactions]
    return TransactionListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )
