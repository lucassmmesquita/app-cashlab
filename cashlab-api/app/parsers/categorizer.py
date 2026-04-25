from __future__ import annotations
"""CashLab — Motor de categorização automática"""
from typing import Optional



# Regras baseadas nos dados reais — ver CLAUDE.md para detalhes
CATEGORIZATION_RULES: dict[str, tuple[str, str]] = {
    # Alimentação
    r"CASA PORTUGUESA|BUTCHER|ALDEOTA RUA|CHURRASCARIA|PIZZA|ERIVALDO":
        ("Alimentação", "Restaurante"),
    r"MERCADINHO|SAM'?S CLUB|ENTRE AMIGOS|SUPERMERCADO|MERCADO":
        ("Supermercado", "Supermercado"),
    r"A[CÇ]A[IÍ]|PITANGA|SORVETE":
        ("Alimentação", "Açaí/Sorvete"),

    # Automotivo / Combustível
    r"STONE\s*C[AE]R|RL\s*AUTO|TOP\s*CAR":
        ("Automotivo", "Peças e Manutenção"),
    r"PETRO\s*CAR|POSTO|SHELL|IPIRANGA":
        ("Combustível", "Combustível"),

    # Assinaturas
    r"APPLE\.COM|APPLE\s*BILL":
        ("Assinaturas e Serviços Digitais", "Apple"),
    r"NETFLIX":
        ("Assinaturas e Serviços Digitais", "Netflix"),
    r"SPOTIFY":
        ("Assinaturas e Serviços Digitais", "Spotify"),

    # Farmácia
    r"PAGUE\s*MENOS|EXTRA\s*FARMA|DROGASIL|FARM[AÁ]CIA":
        ("Farmácia e Saúde", "Farmácia"),

    # Serviços Pessoais
    r"J\s*PESSOA|EST[EÉ]TICA|SAL[AÃ]O":
        ("Serviços Pessoais (Estética)", "Estética"),

    # Tarifas
    r"ANUIDADE|TARIFA|MENSALIDADE\s*CART":
        ("Tarifas Bancárias", "Tarifa"),
}


def categorize_transaction(description: str) -> tuple[Optional[str], Optional[str], float]:
    """
    Categorizar transação pela descrição.
    
    Args:
        description: Descrição da transação
    
    Returns:
        Tuple (categoria, subcategoria, confiança)
        confiança: 0.0 a 1.0
    """
    import re

    description_upper = description.upper().strip()

    for pattern, (category, subcategory) in CATEGORIZATION_RULES.items():
        if re.search(pattern, description_upper):
            return category, subcategory, 0.9

    return "Outros", None, 0.1
