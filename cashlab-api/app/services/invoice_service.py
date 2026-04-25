"""CashLab — Invoice service (processamento de faturas)"""


async def process_invoice_pdf(file_path: str, bank: str = "auto"):
    """Processar PDF de fatura de cartão de crédito"""
    # TODO: Implementar processamento
    # 1. Detectar banco (se auto)
    # 2. Invocar parser específico
    # 3. Categorizar transações
    # 4. Atribuir membros (QUEM)
    # 5. Detectar duplicatas
    pass


async def confirm_invoice_import(task_id: str, adjustments: list):
    """Confirmar importação com ajustes do usuário"""
    # TODO: Implementar confirmação
    pass
