/**
 * CashLab — Tipos de orçamento
 */

export interface Budget {
  id: number;
  category_id: number;
  month: string;
  planned_amount: string;
  actual_amount: string;
}

export interface Income {
  id: number;
  member_id: number | null;
  source: string;
  type: 'CLT' | 'PJ' | 'Benefício';
  amount: string;
  earmarked_for: string | null;
  is_active: boolean;
}

export interface FixedExpense {
  id: number;
  description: string;
  amount: string;
  category_id: number | null;
  recurrence: 'mensal' | 'anual';
  is_active: boolean;
}

export interface DashboardData {
  month: string;
  total_income: string;
  total_fixed_expenses: string;
  total_card_expenses: string;
  balance: string;
  by_category: CategoryBreakdown[];
  by_member: MemberBreakdown[];
  alerts: Alert[];
}

export interface CategoryBreakdown {
  category_name: string;
  total_amount: string;
  percentage: number;
  transaction_count: number;
}

export interface MemberBreakdown {
  member_name: string;
  total_amount: string;
  percentage: number;
}

export interface Alert {
  type: 'critical' | 'warning' | 'info';
  message: string;
}
