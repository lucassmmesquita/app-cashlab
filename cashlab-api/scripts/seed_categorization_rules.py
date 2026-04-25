"""CashLab — Seed de regras de categorização automática

Regras regex para classificar transações de fatura por descrição.
Cada regra mapeia um padrão → categoria.

Uso:
    python -m scripts.seed_categorization_rules

Ou automaticamente no startup (main.py).
"""
import asyncio
from sqlalchemy import select

from app.core.database import async_session_maker, init_db
from app.models import Category, CategorizationRule


# ── Regras de categorização ────────────────────────────────────────
# Formato: (pattern_regex, nome_categoria, subcategoria, prioridade)
# Prioridade maior = testada primeiro dentro do mesmo nível
# Patterns são case-insensitive

RULES = [
    # ── Alimentação ────────────────────────────────────────────────
    (r"IFOOD|I\.FOOD", "Alimentação", "Delivery", 10),
    (r"RAPPI", "Alimentação", "Delivery", 10),
    (r"UBER\s*EATS", "Alimentação", "Delivery", 10),
    (r"RESTAURANTE|REST\.", "Alimentação", "Restaurante", 5),
    (r"PADARIA|PANIFICADORA", "Alimentação", "Padaria", 5),
    (r"LANCHONETE|LANCH\.", "Alimentação", "Lanchonete", 5),
    (r"CASA PORTUGUESA", "Alimentação", "Restaurante", 5),
    (r"MC\s*DONALD|BURGER\s*KING|SUBWAY|HABIB", "Alimentação", "Fast Food", 5),
    (r"PIZZA|PIZZARIA", "Alimentação", "Pizzaria", 5),
    (r"ACAI|SORVETERIA|SORVETE", "Alimentação", "Sobremesa", 3),
    (r"CAFE|STARBUCKS|CAFETERIA", "Alimentação", "Café", 3),

    # ── Supermercado ───────────────────────────────────────────────
    (r"SUPERMERCADO|SUPERMERC|SUPER\s*MERC", "Supermercado", None, 10),
    (r"CARREFOUR|EXTRA\s+HIPER|ASSAI|ATACADAO|ATACAD", "Supermercado", None, 10),
    (r"PAO\s*DE\s*ACUCAR|SAMS\s*CLUB|SAM.*S\s*CLUB", "Supermercado", None, 10),
    (r"MERCADO|MERCEARIA|HORTIFRUTI|SACOLAO", "Supermercado", None, 5),
    (r"MAKRO|BIG\s*BOMPRECO|MATEUS", "Supermercado", None, 5),

    # ── Combustível ────────────────────────────────────────────────
    (r"COMBUSTIVEL|COMBUSTIVEIS|COMBUST", "Combustível", None, 10),
    (r"POSTO|PETROCAR|PETROBRAS|SHELL|IPIRANGA|BR\s+DISTRIB", "Combustível", None, 10),
    (r"GASOLINA|ETANOL|DIESEL|GNV|ABASTEC", "Combustível", None, 8),

    # ── Automotivo ─────────────────────────────────────────────────
    (r"ESTACIONAMENTO|ESTAPAR|PARK", "Estacionamento e Transporte", None, 10),
    (r"PEDAGIO|PEDÁGIO|SEM\s*PARAR|CONECTCAR|VELOE", "Estacionamento e Transporte", "Pedágio", 10),
    (r"OFICINA|MECANICA|FUNILARIA|BORRACHARIA", "Automotivo", "Manutenção", 5),
    (r"PNEU|PIRELLI|GOODYEAR|BRIDGESTONE", "Automotivo", "Pneu", 5),
    (r"LAVA\s*JATO|LAVAGEM", "Automotivo", "Lavagem", 5),
    (r"SEGURO\s*AUTO|SEGURO\s*VEIC", "Seguros", "Auto", 8),

    # ── Transporte ─────────────────────────────────────────────────
    (r"UBER\s*\*TRIP|UBER\s+TRIP|UBER\s+BV", "Estacionamento e Transporte", "Uber", 10),
    (r"99\s*TAXI|99\s*POP|99\s*APP|INDRIVER", "Estacionamento e Transporte", "App Transporte", 10),
    (r"METRO|METRÔ|CPTM|BILHETE\s*UNICO", "Estacionamento e Transporte", "Transporte Público", 5),

    # ── Farmácia e Saúde ───────────────────────────────────────────
    (r"FARMACIA|FARMA|DROGARIA|DROGASIL|DROGA\s*RAIA", "Farmácia e Saúde", "Farmácia", 10),
    (r"EXTRA\s+FARMA|PANVEL|PAGUE\s*MENOS|ULTRAFARMA", "Farmácia e Saúde", "Farmácia", 10),
    (r"HOSPITAL|CLINICA|MEDIC|LABORATORIO|EXAME", "Farmácia e Saúde", "Consulta", 5),
    (r"DENTISTA|ODONTO|ORTODONT", "Farmácia e Saúde", "Dentista", 5),
    (r"OTICA|OCULOS|LENTES", "Farmácia e Saúde", "Ótica", 5),
    (r"ACADEMIA|SMART\s*FIT|BLUE\s*FIT|GYMPASS|WELLHUB", "Farmácia e Saúde", "Academia", 8),

    # ── Compras Online ─────────────────────────────────────────────
    (r"AMAZON|AMZN|AMAZON\.COM", "Compras Online", "Amazon", 10),
    (r"MERCADO\s*LIVRE|MERCADOLIVRE|MELI", "Compras Online", "Mercado Livre", 10),
    (r"SHOPEE|SHEIN|ALIEXPRESS|ALIBABA|TEMU", "Compras Online", "Marketplace", 8),
    (r"MAGAZINE\s*LUIZA|MAGALU|AMERICANAS|CASAS\s*BAHIA", "Compras Online", "Varejo", 5),
    (r"KABUM|PICHAU|TERABYTE", "Compras Online", "Eletrônicos", 5),

    # ── Assinaturas e Serviços Digitais ────────────────────────────
    (r"NETFLIX|DISNEY\+|DISNEY\s*PLUS|HBO|PRIME\s*VIDEO|STAR\+", "Assinaturas e Serviços Digitais", "Streaming", 10),
    (r"SPOTIFY|DEEZER|APPLE\s*MUSIC|YOUTUBE\s*MUSIC|TIDAL", "Assinaturas e Serviços Digitais", "Música", 10),
    (r"APPLE\.COM|APPLE\s*BILL|ITUNES", "Assinaturas e Serviços Digitais", "Apple", 10),
    (r"GOOGLE\s*ONE|GOOGLE\s*PLAY|GOOGLE\s*\*", "Assinaturas e Serviços Digitais", "Google", 10),
    (r"MICROSOFT|XBOX|PLAYSTATION|PSN|STEAM|EPIC\s*GAMES", "Assinaturas e Serviços Digitais", "Games", 8),
    (r"CHATGPT|OPENAI|CLAUDE|MIDJOURNEY", "Assinaturas e Serviços Digitais", "IA", 8),
    (r"DROPBOX|ICLOUD|ONEDRIVE|NOTION|CANVA|FIGMA", "Assinaturas e Serviços Digitais", "Produtividade", 5),
    (r"GLOBOPLAY|TELECINE", "Assinaturas e Serviços Digitais", "Streaming", 8),

    # ── Educação ───────────────────────────────────────────────────
    (r"ESCOLA|COLEGIO|UNIVERSIDADE|FACULDADE", "Educação", None, 10),
    (r"CURSO|UDEMY|COURSERA|ALURA|HOTMART", "Educação", "Curso Online", 8),
    (r"LIVRARIA|LIVRO|SARAIVA|CULTURA", "Educação", "Livros", 5),
    (r"PAPELARIA|KALUNGA", "Educação", "Material", 5),

    # ── Lazer e Entretenimento ─────────────────────────────────────
    (r"CINEMA|CINEMARK|CINEPOLIS|KINOPLEX", "Lazer e Entretenimento", "Cinema", 10),
    (r"TEATRO|SHOW|INGRESSO|TICKET|SYMPLA|EVENTIM", "Lazer e Entretenimento", "Eventos", 8),
    (r"PARQUE|DIVERSAO|ESCAPE\s*ROOM", "Lazer e Entretenimento", "Parque", 5),
    (r"VIAGEM|HOTEL|HOSTEL|AIRBNB|BOOKING|DECOLAR", "Lazer e Entretenimento", "Viagem", 8),
    (r"LATAM|GOL|AZUL|TAM|AVIANCA|PASSAGEM", "Lazer e Entretenimento", "Aéreo", 8),

    # ── Moradia ────────────────────────────────────────────────────
    (r"ALUGUEL|CONDOMINIO|COND\.", "Moradia", "Aluguel/Condomínio", 10),
    (r"ENEL|CPFL|CEMIG|ELETROBRAS|LUZ|ENERGIA", "Moradia", "Energia", 10),
    (r"SABESP|COPASA|EMBASA|AGUA", "Moradia", "Água", 10),
    (r"COMGAS|GAS\s*NATURAL|ULTRAGAS", "Moradia", "Gás", 8),
    (r"INTERNET|NET\s+VIRTUA|VIVO\s+FIBRA|CLARO\s+NET|TIM\s+LIVE", "Moradia", "Internet", 8),
    (r"LEROY\s*MERLIN|TELHANORTE|C\s*&\s*C|CASA\s*SHOW", "Moradia", "Reforma", 5),

    # ── Vestuário ──────────────────────────────────────────────────
    (r"ZARA|H\s*&\s*M|RENNER|C\s*&\s*A|RIACHUELO|MARISA", "Vestuário", None, 10),
    (r"CENTAURO|DECATHLON|NIKE|ADIDAS|PUMA|NETSHOES", "Vestuário", "Esportivo", 8),
    (r"ROUPA|CALCADO|SAPATO|TENIS|MODA", "Vestuário", None, 5),

    # ── Serviços Pessoais ──────────────────────────────────────────
    (r"SALAO|BARBEARIA|CABELEIREIRO|CABELO", "Serviços Pessoais (Estética)", None, 10),
    (r"MANICURE|PEDICURE|ESTETICA|SPA|MASSAGEM", "Serviços Pessoais (Estética)", None, 8),
    (r"DERMATOLOG|DERMA", "Serviços Pessoais (Estética)", "Dermatologia", 5),

    # ── Pets ───────────────────────────────────────────────────────
    (r"PET\s*SHOP|PETSHOP|PETZ|COBASI", "Pets", None, 10),
    (r"VETERINAR|VET\s*CLINIC", "Pets", "Veterinário", 8),
    (r"RACAO|RAÇÃO", "Pets", "Ração", 5),

    # ── Seguros ────────────────────────────────────────────────────
    (r"SEGURO|PORTO\s*SEGURO|SULAMERICA|BRADESCO\s*SEGURO", "Seguros", None, 5),
    (r"UNIMED|AMIL|HAPVIDA|PLANO\s*SAUDE", "Seguros", "Saúde", 8),

    # ── Tarifas Bancárias ──────────────────────────────────────────
    (r"ANUIDADE|TARIFA|IOF|ENCARGOS|JUROS", "Tarifas Bancárias", None, 10),
    (r"MULTA|MORA|ATRASO", "Tarifas Bancárias", "Multa", 5),

    # ── Transferências Pessoais ────────────────────────────────────
    (r"PAG\*|PIX\s|TRANSF|TRANSFERENCIA", "Transferências Pessoais", None, 3),
]


async def seed_rules():
    """Popula as regras de categorização no banco."""
    await init_db()

    async with async_session_maker() as db:
        # Verificar se já existem regras
        result = await db.execute(select(CategorizationRule))
        existing = result.scalars().all()
        if existing:
            print(f"✅ Regras já existem ({len(existing)} encontradas)")
            return

        # Carregar mapa nome→id das categorias
        cat_result = await db.execute(select(Category))
        categories = {cat.name: cat.id for cat in cat_result.scalars().all()}

        if not categories:
            print("❌ Nenhuma categoria encontrada. Execute seed_categories primeiro.")
            return

        count = 0
        skipped = 0
        for pattern, cat_name, subcategory, priority in RULES:
            cat_id = categories.get(cat_name)
            if not cat_id:
                print(f"⚠️  Categoria não encontrada: {cat_name} (pattern: {pattern})")
                skipped += 1
                continue

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
        print(f"✅ {count} regras de categorização criadas ({skipped} ignoradas)")


if __name__ == "__main__":
    asyncio.run(seed_rules())
