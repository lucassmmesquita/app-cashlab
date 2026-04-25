/**
 * CashLab — Transaction service
 */
import api from './api';
import type { TransactionFilters, TransactionListResponse } from '../types/transaction';

export const transactionService = {
  async list(filters: TransactionFilters = {}): Promise<TransactionListResponse> {
    const response = await api.get('/transactions', { params: filters });
    return response.data;
  },

  async getById(id: number) {
    const response = await api.get(`/transactions/${id}`);
    return response.data.data;
  },

  async update(id: number, data: Record<string, any>) {
    const response = await api.put(`/transactions/${id}`, data);
    return response.data.data;
  },

  async delete(id: number) {
    const response = await api.delete(`/transactions/${id}`);
    return response.data;
  },
};
