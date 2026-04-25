/**
 * CashLab — Tipos de transação
 */

export interface Transaction {
  id: number;
  invoice_id: number;
  card_id: number;
  member_id: number | null;
  category_id: number | null;
  transaction_date: string; // ISO 8601
  description: string;
  raw_description: string | null;
  amount: string; // Decimal como string — nunca float
  installment_num: number | null;
  installment_total: number | null;
  subcategory: string | null;
  who: 'LUCAS' | 'JURA' | 'JOICE' | '-' | 'PENDENTE';
  is_international: boolean;
  iof_amount: string | null;
  location: string | null;
  notes: string | null;
}

export interface TransactionFilters {
  month?: string;
  bank?: string;
  member?: string;
  category_id?: string;
  search?: string;
  page?: number;
  per_page?: number;
}

export interface TransactionListResponse {
  data: Transaction[];
  meta: {
    page: number;
    per_page: number;
    total: number;
  };
}
