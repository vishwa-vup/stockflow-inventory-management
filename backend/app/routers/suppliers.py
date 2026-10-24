from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.database import get_db
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.user import User
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from app.auth.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/suppliers", tags=["Suppliers Management"])

@router.get("", response_model=List[SupplierResponse])
def get_suppliers(
    search: Optional[str] = Query(None, description="Search by name, contact, email, or city"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(
        Supplier,
        func.count(Product.id).label("product_count")
    ).outerjoin(Product, Product.supplier_id == Supplier.id).group_by(Supplier.id)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Supplier.name.ilike(s),
                Supplier.contact_person.ilike(s),
                Supplier.email.ilike(s),
                Supplier.phone.ilike(s),
                Supplier.city.ilike(s),
                Supplier.gst_number.ilike(s)
            )
        )

    results = query.order_by(Supplier.name.asc()).all()

    response = []
    for sup, p_count in results:
        sup_dict = {
            "id": sup.id,
            "name": sup.name,
            "contact_person": sup.contact_person,
            "phone": sup.phone,
            "email": sup.email,
            "address": sup.address,
            "city": sup.city,
            "state": sup.state,
            "gst_number": sup.gst_number,
            "product_count": p_count,
            "created_at": sup.created_at,
            "updated_at": sup.updated_at
        }
        response.append(SupplierResponse(**sup_dict))
    return response

@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier_by_id(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found."
        )
    p_count = db.query(func.count(Product.id)).filter(Product.supplier_id == supplier.id).scalar() or 0
    return SupplierResponse(
        id=supplier.id,
        name=supplier.name,
        contact_person=supplier.contact_person,
        phone=supplier.phone,
        email=supplier.email,
        address=supplier.address,
        city=supplier.city,
        state=supplier.state,
        gst_number=supplier.gst_number,
        product_count=p_count,
        created_at=supplier.created_at,
        updated_at=supplier.updated_at
    )

@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    sup_in: SupplierCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    supplier = Supplier(
        name=sup_in.name.strip(),
        contact_person=sup_in.contact_person.strip() if sup_in.contact_person else None,
        phone=sup_in.phone.strip() if sup_in.phone else None,
        email=sup_in.email.strip() if sup_in.email else None,
        address=sup_in.address.strip() if sup_in.address else None,
        city=sup_in.city.strip() if sup_in.city else None,
        state=sup_in.state.strip() if sup_in.state else None,
        gst_number=sup_in.gst_number.strip() if sup_in.gst_number else None
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return SupplierResponse(
        id=supplier.id,
        name=supplier.name,
        contact_person=supplier.contact_person,
        phone=supplier.phone,
        email=supplier.email,
        address=supplier.address,
        city=supplier.city,
        state=supplier.state,
        gst_number=supplier.gst_number,
        product_count=0,
        created_at=supplier.created_at,
        updated_at=supplier.updated_at
    )

@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    sup_in: SupplierUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found."
        )

    if sup_in.name:
        supplier.name = sup_in.name.strip()
    if sup_in.contact_person is not None:
        supplier.contact_person = sup_in.contact_person.strip() if sup_in.contact_person else None
    if sup_in.phone is not None:
        supplier.phone = sup_in.phone.strip() if sup_in.phone else None
    if sup_in.email is not None:
        supplier.email = sup_in.email.strip() if sup_in.email else None
    if sup_in.address is not None:
        supplier.address = sup_in.address.strip() if sup_in.address else None
    if sup_in.city is not None:
        supplier.city = sup_in.city.strip() if sup_in.city else None
    if sup_in.state is not None:
        supplier.state = sup_in.state.strip() if sup_in.state else None
    if sup_in.gst_number is not None:
        supplier.gst_number = sup_in.gst_number.strip() if sup_in.gst_number else None

    db.commit()
    db.refresh(supplier)
    p_count = db.query(func.count(Product.id)).filter(Product.supplier_id == supplier.id).scalar() or 0
    return SupplierResponse(
        id=supplier.id,
        name=supplier.name,
        contact_person=supplier.contact_person,
        phone=supplier.phone,
        email=supplier.email,
        address=supplier.address,
        city=supplier.city,
        state=supplier.state,
        gst_number=supplier.gst_number,
        product_count=p_count,
        created_at=supplier.created_at,
        updated_at=supplier.updated_at
    )

@router.delete("/{supplier_id}", status_code=status.HTTP_200_OK)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found."
        )

    product_count = db.query(func.count(Product.id)).filter(Product.supplier_id == supplier_id).scalar() or 0
    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete supplier '{supplier.name}' because it supplies {product_count} product(s). Please reassign these products first."
        )

    db.delete(supplier)
    db.commit()
    return {"message": f"Supplier '{supplier.name}' successfully deleted."}
