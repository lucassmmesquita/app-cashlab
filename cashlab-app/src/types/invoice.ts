/**
 * CashLab — Tipos de fatura (invoice)
 */

export interface Invoice {
  id: number;
  card_id: number;
  reference_month: string; // "2026-04"
  due_date: string | null;
  total_amount: string;
  status: 'imported' | 'confirmed' | 'rejected';
  parsed_at: string | null;
}

export interface InvoiceUploadResponse {
  task_id: string;
  status: string;
  estimated_seconds: number;
}

export interface InvoicePreview {
  task_id: string;
  status: string;
  detected_bank: string;
  reference_month: string;
  due_date: string | null;
  total_amount: string;
  card_last_digits: string;
  is_duplicate: boolean;
  transactions: TransactionPreviewItem[];
  summary: {
    total_transactions: number;
    by_member: Record<string, number>;
    by_category: Record<string, number>;
  };
}

export interface TransactionPreviewItem {
  temp_id: number;
  date: string;
  raw_description: string;
  description: string;
  amount: string;
  installment_num: number | null;
  installment_total: number | null;
  suggested_category: string | null;
  suggested_subcategory: string | null;
  suggested_member: string | null;
  confidence: number;
  is_international: boolean;
}
