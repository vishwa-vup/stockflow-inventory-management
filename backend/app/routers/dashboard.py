from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.dashboard import (
    DashboardStatsResponse, StockOverviewItem, StockMovementItem,
    CategoryDistributionItem, LowStockAlertItem, ReorderRecommendationItem
)
from app.services.dashboard_service import (
    get_dashboard_stats, get_stock_overview, get_stock_movement,
    get_category_distribution, get_low_stock_alerts, get_reorder_recommendations
)
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard Analytics"])

@router.get("/stats", response_model=DashboardStatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_dashboard_stats(db)

@router.get("/stock-overview", response_model=List[StockOverviewItem])
def get_overview_chart(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_stock_overview(db, limit)

@router.get("/stock-movement", response_model=List[StockMovementItem])
def get_movement_chart(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_stock_movement(db, days)

@router.get("/category-distribution", response_model=List[CategoryDistributionItem])
def get_distribution_chart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_category_distribution(db)

@router.get("/low-stock-alerts", response_model=List[LowStockAlertItem])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_low_stock_alerts(db)

@router.get("/reorder-recommendations", response_model=List[ReorderRecommendationItem])
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_reorder_recommendations(db)
