/**
 * CashLab — Transaction store (Zustand)
 */
import { create } from 'zustand';
import type { TransactionFilters } from '../types/transaction';

interface TransactionState {
  filters: TransactionFilters;
  setFilters: (filters: Partial<TransactionFilters>) => void;
  resetFilters: () => void;
}

const defaultFilters: TransactionFilters = {
  page: 1,
  per_page: 50,
};

export const useTransactionStore = create<TransactionState>((set) => ({
  filters: defaultFilters,

  setFilters: (newFilters) =>
    set((state) => ({
      filters: { ...state.filters, ...newFilters, page: 1 },
    })),

  resetFilters: () => set({ filters: defaultFilters }),
}));
