/**
 * CashLab — Tipos de categoria
 */

export interface Category {
  id: number;
  name: string;
  icon: string | null;
  color: string | null;
  type: 'fixa' | 'variavel';
  is_system: boolean;
}
