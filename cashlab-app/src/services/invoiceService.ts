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
  payment_month: string;
  competence_month: string;
  due_date: string | null;
  total_amount: string;
  card_last_digits: string;
  transaction_count: number;
  transactions: ParsedTransaction[];
}

export interface InvoiceListItem {
  id: number;
  reference_month: string;
  payment_month: string | null;
  competence_month: string | null;
  due_date: string | null;
  total_amount: string;
  status: string;
  card_id: number;
  bank_name: string | null;
  card_last_digits: string | null;
  transaction_count: number;
  file_size: number | null;
  created_at: string | null;
}

export interface InvoiceDetail extends InvoiceListItem {
  transactions: {
    id: number;
    date: string;
    description: string;
    amount: string;
    who: string;
    category_id: number | null;
    category: string | null;
    subcategory: string | null;
    installment_num: number | null;
    installment_total: number | null;
    is_international: boolean;
  }[];
}

export const invoiceService = {
  /**
   * Upload PDF e receber preview das transações extraídas.
   */
  async upload(fileUri: string, fileName: string, bank: string = 'auto', referenceMonth: string = ''): Promise<UploadPreview> {
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

    const params = new URLSearchParams({ bank });
    if (referenceMonth) params.set('reference_month', referenceMonth);

    // Retry with backoff — max 2 attempts
    const maxRetries = 2;
    let lastError: any;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const res = await api.post(`/invoices/upload?${params.toString()}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 120000, // 120s — PDFs grandes podem demorar
        });
        return res.data.data;
      } catch (err: any) {
        lastError = err;
        // Don't retry on client errors (4xx)
        if (err.response?.status && err.response.status >= 400 && err.response.status < 500) {
          throw err;
        }
        // Wait before retrying (exponential backoff)
        if (attempt < maxRetries) {
          const delay = Math.pow(2, attempt) * 1000; // 1s, 2s
          await new Promise(r => setTimeout(r, delay));
        }
      }
    }
    throw lastError;
  },

  /**
   * Confirmar importação das transações.
   */
  async confirmImport(fileId: string): Promise<void> {
    await api.post(`/invoices/upload/${fileId}/confirm`);
  },

  /**
   * Listar faturas importadas com dados enriquecidos.
   */
  async list(): Promise<InvoiceListItem[]> {
    const res = await api.get('/invoices');
    return res.data?.data || [];
  },

  /**
   * Detalhe da fatura com todas as transações.
   */
  async getDetail(id: number): Promise<InvoiceDetail> {
    const res = await api.get(`/invoices/${id}`);
    return res.data?.data;
  },

  /**
   * Excluir fatura (soft delete).
   */
  async remove(id: number): Promise<void> {
    await api.delete(`/invoices/${id}`);
  },
};
