from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.categories import router as categories_router
from app.routers.suppliers import router as suppliers_router
from app.routers.products import router as products_router
from app.routers.inventory import router as inventory_router
from app.routers.dashboard import router as dashboard_router
from app.routers.reports import router as reports_router

__all__ = [
    "auth_router",
    "users_router",
    "categories_router",
    "suppliers_router",
    "products_router",
    "inventory_router",
    "dashboard_router",
    "reports_router",
]
