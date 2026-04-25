/**
 * CashLab — Budget store (Zustand)
 */
import { create } from 'zustand';

interface BudgetState {
  selectedMonth: string;
  setSelectedMonth: (month: string) => void;
}

function getCurrentMonth(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${year}-${month}`;
}

export const useBudgetStore = create<BudgetState>((set) => ({
  selectedMonth: getCurrentMonth(),
  setSelectedMonth: (month) => set({ selectedMonth: month }),
}));
