/**
 * CashLab — Hook para navegação de meses
 */
import { useBudgetStore } from '../store/useBudgetStore';

export function useMonthNavigation() {
  const selectedMonth = useBudgetStore((state) => state.selectedMonth);
  const setSelectedMonth = useBudgetStore((state) => state.setSelectedMonth);

  const goToPreviousMonth = () => {
    const [year, month] = selectedMonth.split('-').map(Number);
    const prevDate = new Date(year, month - 2, 1);
    const newMonth = `${prevDate.getFullYear()}-${String(prevDate.getMonth() + 1).padStart(2, '0')}`;
    setSelectedMonth(newMonth);
  };

  const goToNextMonth = () => {
    const [year, month] = selectedMonth.split('-').map(Number);
    const nextDate = new Date(year, month, 1);
    const newMonth = `${nextDate.getFullYear()}-${String(nextDate.getMonth() + 1).padStart(2, '0')}`;
    setSelectedMonth(newMonth);
  };

  return { selectedMonth, setSelectedMonth, goToPreviousMonth, goToNextMonth };
}
