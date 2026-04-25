from fastapi import APIRouter
from .auth import router as auth_router
from .cards import router as cards_router
from .invoices import router as invoices_router
from .transactions import router as transactions_router
from .budget import router as budget_router
from .reports import router as reports_router
from .dashboard import router as dashboard_router
from .incomes import router as incomes_router
from .fixed_expenses import router as fixed_expenses_router
from .categories import router as categories_router
from .export import router as export_router
from .transactions_import import router as transactions_import_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(cards_router)
api_router.include_router(invoices_router)
api_router.include_router(transactions_router)
api_router.include_router(budget_router)
api_router.include_router(reports_router)
api_router.include_router(dashboard_router)
api_router.include_router(incomes_router)
api_router.include_router(fixed_expenses_router)
api_router.include_router(categories_router)
api_router.include_router(export_router)
api_router.include_router(transactions_import_router)
