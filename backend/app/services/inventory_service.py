from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.product import Product
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import StockInRequest, StockOutRequest

def process_stock_in(db: Session, req: StockInRequest, user: User) -> Transaction:
    product = db.query(Product).filter(Product.id == req.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {req.product_id} not found."
        )
    
    if req.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity for Stock In must be greater than zero."
        )

    previous_stock = product.current_stock
    new_stock = previous_stock + req.quantity

    # If unit purchase price is provided and positive, optionally update product purchase_price
    unit_price = req.unit_purchase_price if req.unit_purchase_price is not None else product.purchase_price
    if req.unit_purchase_price is not None and req.unit_purchase_price >= 0:
        product.purchase_price = req.unit_purchase_price

    product.current_stock = new_stock
    product.updated_at = datetime.now(timezone.utc)

    tx_date = req.date if req.date else datetime.now(timezone.utc)
    tx = Transaction(
        product_id=product.id,
        user_id=user.id,
        transaction_type="STOCK_IN",
        quantity=req.quantity,
        previous_stock=previous_stock,
        new_stock=new_stock,
        unit_price=unit_price,
        reference_number=req.reference_number,
        notes=req.notes,
        created_at=tx_date
    )

    db.add(tx)
    db.commit()
    db.refresh(tx)
    db.refresh(product)
    return tx

def process_stock_out(db: Session, req: StockOutRequest, user: User) -> Transaction:
    product = db.query(Product).filter(Product.id == req.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {req.product_id} not found."
        )
    
    if req.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity for Stock Out must be greater than zero."
        )

    if req.quantity > product.current_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Available quantity: {product.current_stock}."
        )

    previous_stock = product.current_stock
    new_stock = previous_stock - req.quantity

    product.current_stock = new_stock
    product.updated_at = datetime.now(timezone.utc)

    notes_combined = req.notes or ""
    if req.customer_department:
        notes_combined = f"[{req.customer_department}] {notes_combined}".strip()

    tx_date = req.date if req.date else datetime.now(timezone.utc)
    tx = Transaction(
        product_id=product.id,
        user_id=user.id,
        transaction_type="STOCK_OUT",
        quantity=req.quantity,
        previous_stock=previous_stock,
        new_stock=new_stock,
        unit_price=product.selling_price,
        reference_number=req.reference_number,
        notes=notes_combined if notes_combined else None,
        created_at=tx_date
    )

    db.add(tx)
    db.commit()
    db.refresh(tx)
    db.refresh(product)
    return tx
