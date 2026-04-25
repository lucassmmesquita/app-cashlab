/**
 * CashLab — Invoice service (upload de faturas PDF)
 */
import api from './api';
import { Platform } from 'react-native';

export interface ParsedTransaction {
  date: string | null;
  description: string;
  raw_description: string;
  amount: string;
  installment_num: number | null;
  installment_total: number | null;
  is_international: boolean;
  card_last_digits: string | null;
}

export interface UploadPreview {
  file_id: string;
  bank: string;
  reference_month: string;
  due_date: string | null;
  total_amount: string;
  card_last_digits: string;
  transaction_count: number;
  transactions: ParsedTransaction[];
}

export const invoiceService = {
  /**
   * Upload PDF e receber preview das transações extraídas.
   */
  async upload(fileUri: string, fileName: string, bank: string = 'auto'): Promise<UploadPreview> {
    const formData = new FormData();

    if (Platform.OS === 'web') {
      // Web: fetch the blob from the URI
      const response = await fetch(fileUri);
      const blob = await response.blob();
      formData.append('file', blob, fileName);
    } else {
      // Native: use the URI directly
      formData.append('file', {
        uri: fileUri,
        name: fileName,
        type: 'application/pdf',
      } as any);
    }

    const res = await api.post(`/invoices/upload?bank=${bank}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    });

    return res.data.data;
  },

  /**
   * Confirmar importação das transações.
   */
  async confirmImport(fileId: string): Promise<void> {
    await api.post(`/invoices/upload/${fileId}/confirm`);
  },

  /**
   * Listar faturas importadas.
   */
  async list() {
    const response = await api.get('/invoices');
    return response.data.data;
  },
};
