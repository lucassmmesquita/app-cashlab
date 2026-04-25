"""CashLab — PDF processing task (Celery)"""


def process_pdf_task(file_path: str, bank: str = "auto"):
    """
    Task assíncrona para processar PDF de fatura.
    
    Fluxo:
    1. Detectar banco (se auto)
    2. Invocar parser específico
    3. Categorizar transações
    4. Atribuir membros (QUEM)
    5. Verificar duplicatas
    6. Armazenar resultado para preview
    
    Args:
        file_path: Caminho do PDF
        bank: 'bv', 'itau', 'nubank' ou 'auto'
    """
    # TODO: Implementar com Celery quando Redis estiver disponível
    # Por enquanto, processamento síncrono no endpoint
    pass
