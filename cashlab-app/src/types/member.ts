/**
 * CashLab — Tipos de membro da família
 */

export type MemberName = 'LUCAS' | 'JURA' | 'JOICE';
export type WhoValue = MemberName | '-' | 'PENDENTE';

export interface Member {
  id: number;
  name: MemberName;
  color: string | null;
  avatar_url: string | null;
}

export interface CreditCard {
  id: number;
  member_id: number;
  bank: 'bv' | 'itau' | 'nubank';
  last_digits: string;
  brand: string | null;
  limit_total: string | null;
  due_day: number | null;
  is_active: boolean;
}
