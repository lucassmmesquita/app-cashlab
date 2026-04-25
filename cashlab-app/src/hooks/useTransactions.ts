/**
 * CashLab — Hook para listagem de transações
 */
import { transactionService } from '../services/transactionService';
import { useTransactionStore } from '../store/useTransactionStore';

export function useTransactions() {
  const filters = useTransactionStore((state) => state.filters);
  const setFilters = useTransactionStore((state) => state.setFilters);

  const fetchTransactions = async () => {
    return transactionService.list(filters);
  };

  return { filters, setFilters, fetchTransactions };
}
