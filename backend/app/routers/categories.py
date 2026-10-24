from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.auth.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/categories", tags=["Categories Management"])

@router.get("", response_model=List[CategoryResponse])
def get_categories(
    search: Optional[str] = Query(None, description="Search by category name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(
        Category,
        func.count(Product.id).label("product_count")
    ).outerjoin(Product, Product.category_id == Category.id).group_by(Category.id)

    if search:
        query = query.filter(Category.name.ilike(f"%{search.strip()}%"))

    results = query.order_by(Category.name.asc()).all()
    
    response = []
    for cat, p_count in results:
        cat_dict = {
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "product_count": p_count,
            "created_at": cat.created_at,
            "updated_at": cat.updated_at
        }
        response.append(CategoryResponse(**cat_dict))
    return response

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    cat_in: CategoryCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    existing = db.query(Category).filter(func.lower(Category.name) == cat_in.name.strip().lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{cat_in.name}' already exists."
        )

    category = Category(
        name=cat_in.name.strip(),
        description=cat_in.description.strip() if cat_in.description else None
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        product_count=0,
        created_at=category.created_at,
        updated_at=category.updated_at
    )

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    cat_in: CategoryUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found."
        )

    if cat_in.name and cat_in.name.strip().lower() != category.name.lower():
        existing = db.query(Category).filter(
            func.lower(Category.name) == cat_in.name.strip().lower(),
            Category.id != category_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another category with name '{cat_in.name}' already exists."
            )
        category.name = cat_in.name.strip()

    if cat_in.description is not None:
        category.description = cat_in.description.strip() if cat_in.description else None

    db.commit()
    db.refresh(category)

    p_count = db.query(func.count(Product.id)).filter(Product.category_id == category.id).scalar() or 0
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        product_count=p_count,
        created_at=category.created_at,
        updated_at=category.updated_at
    )

@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found."
        )

    product_count = db.query(func.count(Product.id)).filter(Product.category_id == category_id).scalar() or 0
    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category '{category.name}' because it contains {product_count} product(s). Please reassign or remove these products first."
        )

    db.delete(category)
    db.commit()
    return {"message": f"Category '{category.name}' successfully deleted."}
