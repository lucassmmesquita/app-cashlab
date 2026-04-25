"""CashLab — Export endpoints"""
from fastapi import APIRouter, Query

router = APIRouter(prefix="/export", tags=["Exportação"])


@router.get("/excel")
async def export_excel(month: str = Query(...)):
    """Exportar como Excel"""
    return {"status": "not_implemented"}


@router.get("/csv")
async def export_csv(month: str = Query(...)):
    """Exportar como CSV"""
    return {"status": "not_implemented"}
