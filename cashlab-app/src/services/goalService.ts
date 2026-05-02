/**
 * CashLab — Goal service (metas de redução de gastos)
 */
import api from './api';

export interface GoalItem {
  id: number;
  name: string;
  card_id: number | null;
  target_reduction_pct: number;
  baseline_month: string;
  baseline_amount: string;
  target_amount: string;
  target_month: string;
  status: 'active' | 'achieved' | 'missed' | 'cancelled';
  current_amount?: string;
  progress_pct?: number;
  created_at: string | null;
}

export interface GoalProgress {
  current_amount_fatura: string;
  current_amount_weekly: string;
  current_amount_total: string;
  baseline_amount: string;
  target_amount: string;
  projected_month_end: string;
  progress_pct: number;
  goal_status: 'dentro' | 'risco' | 'fora';
  days_elapsed: number;
  days_in_month: number;
  top_categories: {
    category: string;
    amount: string;
    transaction_count: number;
  }[];
  projections: {
    month: string;
    label: string;
    projected_amount: string;
    target_amount: string;
    within_target: boolean;
  }[];
  feedback: {
    emoji: string;
    title: string;
    message: string;
    type: 'success' | 'warning' | 'critical';
  };
}

export interface GoalDetail extends Omit<GoalItem, 'progress_pct'>, GoalProgress {}

export const goalService = {
  async list(status?: string): Promise<GoalItem[]> {
    const params = status ? { status } : {};
    const res = await api.get('/goals', { params });
    return res.data?.data || [];
  },

  async get(id: number): Promise<GoalDetail> {
    const res = await api.get(`/goals/${id}`);
    return res.data?.data;
  },

  async getProgress(id: number): Promise<GoalProgress> {
    const res = await api.get(`/goals/${id}/progress`);
    return res.data?.data;
  },

  async create(data: {
    card_id?: number;
    target_reduction_pct: number;
    baseline_month: string;
    target_month: string;
    name?: string;
  }): Promise<GoalItem> {
    const res = await api.post('/goals', data);
    return res.data?.data;
  },

  async update(id: number, data: {
    target_reduction_pct?: number;
    target_month?: string;
    name?: string;
    status?: string;
  }): Promise<GoalItem> {
    const res = await api.put(`/goals/${id}`, data);
    return res.data?.data;
  },

  async remove(id: number): Promise<void> {
    await api.delete(`/goals/${id}`);
  },
};
