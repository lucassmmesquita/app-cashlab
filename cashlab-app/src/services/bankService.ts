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
  closing_day: number | null;
  due_day: number | null;
}

export const bankService = {
  async list(): Promise<BankItem[]> {
    const res = await api.get('/banks');
    return res.data?.data || [];
  },

  async create(name: string, color: string, closing_day?: number, due_day?: number): Promise<BankItem> {
    const res = await api.post('/banks', { name, color, closing_day, due_day });
    return res.data?.data;
  },

  async remove(id: number): Promise<void> {
    await api.delete(`/banks/${id}`);
  },
};
