/**
 * CashLab — Budget service
 */
import api from './api';

export const budgetService = {
  async getByMonth(month: string) {
    const response = await api.get(`/budget/${month}`);
    return response.data.data;
  },

  async update(month: string, data: Record<string, any>) {
    const response = await api.put(`/budget/${month}`, data);
    return response.data.data;
  },

  async getVsActual(month: string) {
    const response = await api.get(`/budget/${month}/vs-actual`);
    return response.data.data;
  },
};
