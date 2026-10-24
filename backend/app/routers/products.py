import math
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from app.database import get_db
from app.models.product import Product
from app.models.category import Category
from app.models.supplier import Supplier
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse
from app.auth.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/products", tags=["Products Management"])

def determine_status(current_stock: int, minimum_stock: int) -> str:
    if current_stock == 0:
        return "OUT_OF_STOCK"
    elif current_stock <= minimum_stock:
        return "LOW_STOCK"
    return "IN_STOCK"

def build_product_response(p: Product) -> ProductResponse:
    stat = determine_status(p.current_stock, p.minimum_stock)
    inv_value = round(p.current_stock * p.purchase_price, 2)
    return ProductResponse(
        id=p.id,
        product_code=p.product_code,
        name=p.name,
        description=p.description,
        category_id=p.category_id,
        supplier_id=p.supplier_id,
        category_name=p.category.name if p.category else "Unassigned",
        supplier_name=p.supplier.name if p.supplier else "Unassigned",
        purchase_price=round(p.purchase_price, 2),
        selling_price=round(p.selling_price, 2),
        current_stock=p.current_stock,
        minimum_stock=p.minimum_stock,
        maximum_stock=p.maximum_stock,
        location=p.location,
        status=stat,
        inventory_value=inv_value,
        created_at=p.created_at,
        updated_at=p.updated_at
    )

@router.get("", response_model=ProductListResponse)
def get_products(
    search: Optional[str] = Query(None, description="Search by product name or code"),
    category_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    stock_status: Optional[str] = Query(None, description="IN_STOCK, LOW_STOCK, OUT_OF_STOCK"),
    sort_by: Optional[str] = Query("created_at", description="price, stock, name, code, created_at"),
    sort_order: Optional[str] = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Product)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(or_(Product.name.ilike(s), Product.product_code.ilike(s)))

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if supplier_id:
        query = query.filter(Product.supplier_id == supplier_id)

    # Status filtering
    if stock_status:
        stat_upper = stock_status.upper().strip()
        if stat_upper == "OUT_OF_STOCK":
            query = query.filter(Product.current_stock == 0)
        elif stat_upper == "LOW_STOCK":
            query = query.filter(Product.current_stock > 0, Product.current_stock <= Product.minimum_stock)
        elif stat_upper == "IN_STOCK":
            query = query.filter(Product.current_stock > Product.minimum_stock)

    # Sorting
    sort_column = Product.created_at
    if sort_by == "price":
        sort_column = Product.selling_price
    elif sort_by == "stock":
        sort_column = Product.current_stock
    elif sort_by == "name":
        sort_column = Product.name
    elif sort_by == "code":
        sort_column = Product.product_code

    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    total = query.count()
    offset = (page - 1) * limit
    products = query.offset(offset).limit(limit).all()
    total_pages = math.ceil(total / limit) if limit > 0 else 1

    items = [build_product_response(p) for p in products]
    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found."
        )
    return build_product_response(product)

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    p_in: ProductCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    # Unique product code validation
    existing_code = db.query(Product).filter(Product.product_code == p_in.product_code.strip()).first()
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with code '{p_in.product_code}' already exists. Product codes must be unique."
        )

    # Check category existence
    cat = db.query(Category).filter(Category.id == p_in.category_id).first()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Selected Category with ID {p_in.category_id} does not exist."
        )

    # Check supplier existence
    sup = db.query(Supplier).filter(Supplier.id == p_in.supplier_id).first()
    if not sup:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Selected Supplier with ID {p_in.supplier_id} does not exist."
        )

    product = Product(
        product_code=p_in.product_code.strip().upper(),
        name=p_in.name.strip(),
        description=p_in.description.strip() if p_in.description else None,
        category_id=p_in.category_id,
        supplier_id=p_in.supplier_id,
        purchase_price=p_in.purchase_price,
        selling_price=p_in.selling_price,
        current_stock=p_in.initial_stock,
        minimum_stock=p_in.minimum_stock,
        maximum_stock=p_in.maximum_stock,
        location=p_in.location.strip() if p_in.location else None
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # If initial stock was provided, create an opening stock transaction
    if p_in.initial_stock > 0:
        opening_tx = Transaction(
            product_id=product.id,
            user_id=admin.id,
            transaction_type="STOCK_IN",
            quantity=p_in.initial_stock,
            previous_stock=0,
            new_stock=p_in.initial_stock,
            unit_price=p_in.purchase_price,
            reference_number="INITIAL_OPENING_STOCK",
            notes=f"Initial stock entered upon product creation by {admin.name}",
            created_at=datetime.now(timezone.utc)
        )
        db.add(opening_tx)
        db.commit()

    return build_product_response(product)

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    p_in: ProductUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found."
        )

    if p_in.product_code and p_in.product_code.strip().upper() != product.product_code:
        code_check = db.query(Product).filter(
            Product.product_code == p_in.product_code.strip().upper(),
            Product.id != product_id
        ).first()
        if code_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with code '{p_in.product_code}' already exists."
            )
        product.product_code = p_in.product_code.strip().upper()

    if p_in.name:
        product.name = p_in.name.strip()
    if p_in.description is not None:
        product.description = p_in.description.strip() if p_in.description else None

    if p_in.category_id:
        cat = db.query(Category).filter(Category.id == p_in.category_id).first()
        if not cat:
            raise HTTPException(status_code=400, detail=f"Category ID {p_in.category_id} does not exist.")
        product.category_id = p_in.category_id

    if p_in.supplier_id:
        sup = db.query(Supplier).filter(Supplier.id == p_in.supplier_id).first()
        if not sup:
            raise HTTPException(status_code=400, detail=f"Supplier ID {p_in.supplier_id} does not exist.")
        product.supplier_id = p_in.supplier_id

    if p_in.purchase_price is not None:
        product.purchase_price = p_in.purchase_price
    if p_in.selling_price is not None:
        product.selling_price = p_in.selling_price
    if p_in.minimum_stock is not None:
        product.minimum_stock = p_in.minimum_stock
    if p_in.maximum_stock is not None:
        product.maximum_stock = p_in.maximum_stock

    if product.maximum_stock <= product.minimum_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum stock must be strictly greater than minimum stock."
        )

    if p_in.location is not None:
        product.location = p_in.location.strip() if p_in.location else None

    product.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(product)
    return build_product_response(product)

@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found."
        )

    p_name = product.name
    db.delete(product)
    db.commit()
    return {"message": f"Product '{p_name}' successfully deleted."}
