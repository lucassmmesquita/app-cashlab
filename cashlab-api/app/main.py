# Load environment variables from .env file
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core import settings, init_db, hash_password
from app.core.database import async_session_maker, engine
from app.api.v1 import api_router
from app.models import User, FamilyGroup, Member, Category


async def auto_migrate():
    """
    Auto-migrate: adiciona colunas/tabelas novas.
    Cada SQL roda em sua própria transação (Postgres exige isso para ignorar erros).
    Usa ADD COLUMN IF NOT EXISTS (PostgreSQL 9.6+).
    """
    from sqlalchemy import text

    migrations = [
        "ALTER TABLE incomes ADD COLUMN IF NOT EXISTS effective_from VARCHAR(7) DEFAULT NULL",
        "ALTER TABLE incomes ADD COLUMN IF NOT EXISTS effective_until VARCHAR(7) DEFAULT NULL",
        "ALTER TABLE fixed_expenses ADD COLUMN IF NOT EXISTS effective_from VARCHAR(7) DEFAULT NULL",
        "ALTER TABLE fixed_expenses ADD COLUMN IF NOT EXISTS effective_until VARCHAR(7) DEFAULT NULL",
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS source_type VARCHAR(20) NOT NULL DEFAULT 'FATURA'",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS source_type VARCHAR(20) NOT NULL DEFAULT 'PDF'",
        """CREATE TABLE IF NOT EXISTS spending_goals (
            id SERIAL PRIMARY KEY,
            family_group_id INTEGER NOT NULL REFERENCES family_groups(id),
            card_id INTEGER REFERENCES credit_cards(id),
            target_reduction_pct INTEGER NOT NULL,
            baseline_month VARCHAR(7) NOT NULL,
            baseline_amount NUMERIC(12,2) NOT NULL,
            target_amount NUMERIC(12,2) NOT NULL,
            target_month VARCHAR(7) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            name VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            deleted_at TIMESTAMP WITH TIME ZONE
        )""",
        """CREATE TABLE IF NOT EXISTS goal_snapshots (
            id SERIAL PRIMARY KEY,
            goal_id INTEGER NOT NULL REFERENCES spending_goals(id),
            snapshot_date DATE NOT NULL,
            current_amount NUMERIC(12,2) NOT NULL,
            source VARCHAR(20) NOT NULL DEFAULT 'FATURA',
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )""",
        "CREATE INDEX IF NOT EXISTS idx_incomes_effective_from ON incomes(effective_from)",
        "CREATE INDEX IF NOT EXISTS idx_fixed_expenses_effective_from ON fixed_expenses(effective_from)",
        "CREATE INDEX IF NOT EXISTS idx_spending_goals_family ON spending_goals(family_group_id)",
        "CREATE INDEX IF NOT EXISTS idx_goal_snapshots_goal ON goal_snapshots(goal_id)",
        "UPDATE incomes SET effective_from = '2026-03' WHERE effective_from IS NULL",
        "UPDATE fixed_expenses SET effective_from = '2026-03' WHERE effective_from IS NULL",
        # v2.0 — Parser training lifecycle
        "ALTER TABLE banks ADD COLUMN IF NOT EXISTS parser_status VARCHAR(20) NOT NULL DEFAULT 'pending'",
        "ALTER TABLE banks ADD COLUMN IF NOT EXISTS parser_trained_at TIMESTAMP WITH TIME ZONE DEFAULT NULL",
        "UPDATE banks SET parser_status = 'ready' WHERE has_native_parser = true AND parser_status = 'pending'",
        # v2.0 — Competência vs Pagamento
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS payment_month VARCHAR(7) DEFAULT NULL",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS competence_month VARCHAR(7) DEFAULT NULL",
        "CREATE INDEX IF NOT EXISTS idx_invoices_payment_month ON invoices(payment_month)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_competence_month ON invoices(competence_month)",
    ]

    for sql in migrations:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(sql))
        except Exception:
            pass

    print("✅ Auto-migrate complete")


async def seed_initial_data():
    """Seed database with initial data — handles race conditions"""
    async with async_session_maker() as db:
        # Seed categorias
        try:
            result = await db.execute(select(Category))
            categories = result.scalars().all()

            if not categories:
                from scripts.seed_categories import CATEGORIES
                for cat_data in CATEGORIES:
                    cat = Category(**cat_data, is_system=True)
                    db.add(cat)
                await db.commit()
                print(f"✅ {len(CATEGORIES)} categorias criadas")
        except IntegrityError:
            await db.rollback()

        # Seed grupo familiar + membros
        try:
            result = await db.execute(select(FamilyGroup))
            family = result.scalar_one_or_none()

            if not family:
                family = FamilyGroup(name="Família CashLab")
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
                print(f"✅ Grupo '{family.name}' criado com 3 membros")
        except IntegrityError:
            await db.rollback()

        # Seed admin user
        try:
            result = await db.execute(
                select(User).where(User.email == "admin@cashlab.app")
            )
            admin = result.scalar_one_or_none()

            if not admin:
                admin = User(
                    email="admin@cashlab.app",
                    password_hash=hash_password("admin123"),
                    name="Administrador",
                    family_group_id=family.id if family else None,
                    is_active=True,
                )
                db.add(admin)
                await db.commit()
                print("✅ Usuário admin criado (admin@cashlab.app / admin123)")
        except IntegrityError:
            await db.rollback()

        # Seed regras de categorização
        try:
            from app.models import CategorizationRule
            result = await db.execute(select(CategorizationRule))
            existing_rules = result.scalars().all()

            if not existing_rules:
                from scripts.seed_categorization_rules import RULES
                # Carregar mapa nome→id das categorias
                cat_result = await db.execute(select(Category))
                cat_map = {cat.name: cat.id for cat in cat_result.scalars().all()}

                count = 0
                for pattern, cat_name, subcategory, priority in RULES:
                    cat_id = cat_map.get(cat_name)
                    if cat_id:
                        rule = CategorizationRule(
                            pattern=pattern,
                            category_id=cat_id,
                            subcategory=subcategory,
                            priority=priority,
                            is_user_rule=False,
                        )
                        db.add(rule)
                        count += 1
                await db.commit()
                print(f"✅ {count} regras de categorização criadas")
        except IntegrityError:
            await db.rollback()

        # Seed receitas mensais
        try:
            from app.models import Income
            result = await db.execute(select(Income))
            existing_incomes = result.scalars().all()

            if not existing_incomes:
                fg_result = await db.execute(select(FamilyGroup))
                fg = fg_result.scalar_one_or_none()
                fg_id = fg.id if fg else 1

                incomes_data = [
                    {"source": "iRede CLT", "type": "CLT", "amount": 6700.00, "earmarked_for": "Salário registrado", "effective_from": "2026-03"},
                    {"source": "iRede PJ", "type": "PJ", "amount": 17500.00, "earmarked_for": "Pró-labore / nota fiscal", "effective_from": "2026-03"},
                    {"source": "Totalis", "type": "PJ/Extra", "amount": 2000.00, "earmarked_for": "Receita adicional", "effective_from": "2026-03"},
                ]
                for inc_data in incomes_data:
                    income = Income(family_group_id=fg_id, **inc_data)
                    db.add(income)
                await db.commit()
                print(f"✅ {len(incomes_data)} receitas mensais criadas")
        except IntegrityError:
            await db.rollback()

        # Seed despesas fixas mensais
        try:
            from app.models import FixedExpense
            result = await db.execute(select(FixedExpense))
            existing_expenses = result.scalars().all()

            if not existing_expenses:
                fg_result = await db.execute(select(FamilyGroup))
                fg = fg_result.scalar_one_or_none()
                fg_id = fg.id if fg else 1

                expenses_data = [
                    {"description": "Aluguel + Cond + Água + Gás", "amount": 4645.50, "recurrence": "Moradia", "effective_from": "2026-03"},
                    {"description": "Financiamento do carro", "amount": 1650.42, "recurrence": "Automotivo", "effective_from": "2026-03"},
                    {"description": "Energia elétrica (média)", "amount": 800.00, "recurrence": "Moradia", "effective_from": "2026-03"},
                    {"description": "Ajuda Pais da Joice", "amount": 500.00, "recurrence": "Família", "effective_from": "2026-03"},
                    {"description": "Ajuda Pais do Lucas", "amount": 500.00, "recurrence": "Família", "effective_from": "2026-03"},
                ]
                for exp_data in expenses_data:
                    expense = FixedExpense(family_group_id=fg_id, **exp_data)
                    db.add(expense)
                await db.commit()
                print(f"✅ {len(expenses_data)} despesas fixas mensais criadas")
        except IntegrityError:
            await db.rollback()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_db()
    await auto_migrate()
    await seed_initial_data()
    yield
    # Shutdown
    pass


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CashLab — API de controle financeiro familiar com importação de faturas PDF",
    lifespan=lifespan,
)

# CORS middleware
import os
cors_origins_env = os.getenv("CORS_ORIGINS", "")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()] if cors_origins_env else []
default_origins = [
    "http://localhost:8081",
    "http://localhost:19006",
    "http://localhost:19000",
]
all_origins = list(set(cors_origins + default_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=all_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
uploads_path = Path("uploads")
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
