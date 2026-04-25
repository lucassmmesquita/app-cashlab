/**
 * CashLab — Report service (dashboard e relatórios)
 */
import api from './api';
import type { DashboardData } from '../types/budget';

export const reportService = {
  async getDashboard(month: string): Promise<DashboardData> {
    const response = await api.get(`/dashboard/${month}`);
    return response.data.data;
  },

  async byCategory(month: string) {
    const response = await api.get('/reports/by-category', { params: { month } });
    return response.data.data;
  },

  async byMember(month: string) {
    const response = await api.get('/reports/by-member', { params: { month } });
    return response.data.data;
  },

  async installments() {
    const response = await api.get('/reports/installments');
    return response.data.data;
  },

  async subscriptions() {
    const response = await api.get('/reports/subscriptions');
    return response.data.data;
  },
};
