/**
 * CashLab — Hook para dados do dashboard
 */
import { reportService } from '../services/reportService';
import { useBudgetStore } from '../store/useBudgetStore';

export function useDashboard() {
  const selectedMonth = useBudgetStore((state) => state.selectedMonth);

  const fetchDashboard = async () => {
    return reportService.getDashboard(selectedMonth);
  };

  return { selectedMonth, fetchDashboard };
}
