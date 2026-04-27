/**
 * CashLab — Bank service (CRUD completo de bancos)
 *
 * v2.0: Adicionados getDetail, update, retrain, createWithPdf.
 */
import api from './api';
import { Platform } from 'react-native';

export interface BankItem {
  id: number;
  name: string;
  slug: string;
  color: string;
  status: 'ready' | 'pending';
  has_native_parser: boolean;
  closing_day: number | null;
  due_day: number | null;
  parser_status: 'pending' | 'processing' | 'ready' | 'error';
  parser_trained_at: string | null;
  invoice_count: number;
}

export const bankService = {
  async list(): Promise<BankItem[]> {
    const res = await api.get('/banks');
    return res.data?.data || [];
  },

  async getDetail(id: number): Promise<BankItem> {
    const res = await api.get(`/banks/${id}`);
    return res.data?.data;
  },

  async create(name: string, color: string, closing_day?: number, due_day?: number): Promise<BankItem> {
    const res = await api.post('/banks', { name, color, closing_day, due_day });
    return res.data?.data;
  },

  async update(id: number, data: { name?: string; color?: string; closing_day?: number; due_day?: number }): Promise<BankItem> {
    const res = await api.put(`/banks/${id}`, data);
    return res.data?.data;
  },

  async retrain(id: number, fileUri: string, fileName: string): Promise<BankItem & { message?: string }> {
    const formData = new FormData();

    if (Platform.OS === 'web') {
      const response = await fetch(fileUri);
      const blob = await response.blob();
      formData.append('file', blob, fileName);
    } else {
      formData.append('file', {
        uri: fileUri,
        name: fileName,
        type: 'application/pdf',
      } as any);
    }

    const res = await api.post(`/banks/${id}/retrain`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
    return res.data?.data;
  },

  async remove(id: number): Promise<void> {
    await api.delete(`/banks/${id}`);
  },
};
