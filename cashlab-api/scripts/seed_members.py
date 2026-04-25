"""CashLab — Seed de membros iniciais"""
import asyncio
from sqlalchemy import select

from app.core.database import async_session_maker, init_db
from app.models import FamilyGroup, Member


async def seed_members():
    """Popula grupo familiar e membros com dados reais"""
    await init_db()
    
    async with async_session_maker() as db:
        # Criar grupo familiar
        result = await db.execute(select(FamilyGroup))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"✅ Grupo familiar já existe: {existing.name}")
            return

        family = FamilyGroup(name="Família Mesquita")
        db.add(family)
        await db.flush()

        members_data = [
            {"name": "LUCAS", "color": "#4A90D9"},
            {"name": "JURA", "color": "#E94E77"},
            {"name": "JOICE", "color": "#50C878"},
        ]

        for m_data in members_data:
            member = Member(family_group_id=family.id, **m_data)
            db.add(member)

        await db.commit()
        print(f"✅ Grupo '{family.name}' criado com {len(members_data)} membros")


if __name__ == "__main__":
    asyncio.run(seed_members())
