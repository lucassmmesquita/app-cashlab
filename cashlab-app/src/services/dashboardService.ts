/**
 * CashLab — Dashboard service (dados reais do backend)
 */
import api from './api';

export interface DashboardInsight {
  type: 'info' | 'warning' | 'critical';
  title: string;
  message: string;
}

export interface DashboardCardBreakdown {
  bank: string;
  last_digits: string;
  total_amount: string;
  transaction_count: number;
  percentage: number;
}

export interface DashboardResponse {
  month: string;
  total_income: string;
  total_fixed_expenses: string;
  total_card_expenses: string;
  total_weekly_expenses: string;
  total_expenses: string;
  balance: string;
  by_category: {
    category_name: string;
    total_amount: string;
    percentage: number;
    transaction_count: number;
  }[];
  by_member: {
    member_name: string;
    total_amount: string;
    percentage: number;
  }[];
  by_card: DashboardCardBreakdown[];
  insights: DashboardInsight[];
  alerts: {
    type: 'critical' | 'warning' | 'info';
    message: string;
  }[];
}

export const dashboardService = {
  /**
   * Buscar dados consolidados do dashboard para um mês.
   */
  async get(month: string): Promise<DashboardResponse> {
    const res = await api.get(`/dashboard/${month}`, { timeout: 90000 });
    return res.data?.data;
  },
};
