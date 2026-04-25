/**
 * CashLab — Formatadores para valores financeiros, datas e percentuais
 * Formatação pt-BR: R$ 1.234,56
 */

/**
 * Formata valor como moeda brasileira
 * Backend envia "1234.56" → exibe "R$ 1.234,56"
 */
export function formatCurrency(value: string | number): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return 'R$ 0,00';

  return num.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/**
 * Formata data ISO para formato brasileiro
 * "2026-04-15" → "15/04/2026"
 */
export function formatDate(isoDate: string): string {
  if (!isoDate) return '';
  const [year, month, day] = isoDate.split('T')[0].split('-');
  return `${day}/${month}/${year}`;
}

/**
 * Formata data ISO para formato curto
 * "2026-04-15" → "15/04"
 */
export function formatDateShort(isoDate: string): string {
  if (!isoDate) return '';
  const [, month, day] = isoDate.split('T')[0].split('-');
  return `${day}/${month}`;
}

/**
 * Formata mês de referência
 * "2026-04" → "Abril 2026"
 */
export function formatReferenceMonth(month: string): string {
  const MONTHS = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
  ];
  const [year, m] = month.split('-');
  const monthIndex = parseInt(m, 10) - 1;
  return `${MONTHS[monthIndex]} ${year}`;
}

/**
 * Formata percentual
 * 0.2734 → "27,3%"
 */
export function formatPercent(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals).replace('.', ',')}%`;
}

/**
 * Formata parcela
 * (3, 10) → "3/10"
 */
export function formatInstallment(num: number | null, total: number | null): string {
  if (num == null || total == null) return '';
  return `${num}/${total}`;
}
