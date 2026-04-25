/**
 * CashLab — Bank service (CRUD de bancos)
 */
import api from './api';

export interface BankItem {
  id: number;
  name: string;
  slug: string;
  color: string;
  status: 'ready' | 'pending';
  has_native_parser: boolean;
}

export const bankService = {
  async list(): Promise<BankItem[]> {
    const res = await api.get('/banks');
    return res.data?.data || [];
  },

  async create(name: string, color: string): Promise<BankItem> {
    const res = await api.post('/banks', { name, color });
    return res.data?.data;
  },

  async remove(id: number): Promise<void> {
    await api.delete(`/banks/${id}`);
  },
};
