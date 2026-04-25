"""CashLab — Seed de categorias iniciais (18 categorias)"""
import asyncio
from sqlalchemy import select

from app.core.database import async_session_maker, init_db
from app.models import Category


CATEGORIES = [
    {"name": "Alimentação", "icon": "food", "type": "variavel"},
    {"name": "Assinaturas e Serviços Digitais", "icon": "subscription", "type": "fixa"},
    {"name": "Automotivo", "icon": "car", "type": "variavel"},
    {"name": "Combustível", "icon": "fuel", "type": "variavel"},
    {"name": "Compras Online", "icon": "shopping-cart", "type": "variavel"},
    {"name": "Educação", "icon": "book", "type": "variavel"},
    {"name": "Estacionamento e Transporte", "icon": "parking", "type": "variavel"},
    {"name": "Farmácia e Saúde", "icon": "medical", "type": "variavel"},
    {"name": "Lazer e Entretenimento", "icon": "gamepad", "type": "variavel"},
    {"name": "Moradia", "icon": "home", "type": "fixa"},
    {"name": "Pets", "icon": "paw", "type": "variavel"},
    {"name": "Seguros", "icon": "shield", "type": "fixa"},
    {"name": "Serviços Pessoais (Estética)", "icon": "scissors", "type": "variavel"},
    {"name": "Supermercado", "icon": "cart", "type": "variavel"},
    {"name": "Transferências Pessoais", "icon": "transfer", "type": "variavel"},
    {"name": "Vestuário", "icon": "shirt", "type": "variavel"},
    {"name": "Tarifas Bancárias", "icon": "bank", "type": "fixa"},
    {"name": "Outros", "icon": "help-circle", "type": "variavel"},
]


async def seed_categories():
    """Popula as 18 categorias do CashLab"""
    await init_db()
    
    async with async_session_maker() as db:
        result = await db.execute(select(Category))
        existing = result.scalars().all()

        if existing:
            print(f"✅ Categorias já existem ({len(existing)} encontradas)")
            return

        for cat_data in CATEGORIES:
            cat = Category(**cat_data, is_system=True)
            db.add(cat)

        await db.commit()
        print(f"✅ {len(CATEGORIES)} categorias criadas com sucesso")


if __name__ == "__main__":
    asyncio.run(seed_categories())
