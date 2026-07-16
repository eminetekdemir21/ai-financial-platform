import { apiClient } from "./client";

export interface SpendingTrend {
  category: string;
  current_monthly: string;
  previous_monthly: string;
  change_pct: number;
  trend: "artiyor" | "azaliyor" | "stabil";
}

export interface SavingTip {
  category: string;
  title: string;
  description: string;
  monthly_saving_potential: string;
  annual_saving_potential: string;
  difficulty: string;
  priority: string;
}

export interface SavingsCoachReport {
  total_monthly_income: string;
  total_monthly_expense: string;
  current_savings_rate: number;
  target_savings_rate: number;
  monthly_savings_gap: string;
  spending_trends: SpendingTrend[];
  tips: SavingTip[];
  coach_message: string;
  potential_annual_savings: string;
}

export async function getSavingsReport(accountId: string): Promise<SavingsCoachReport> {
  const { data } = await apiClient.get(`/savings-coach/${accountId}`);
  return data;
}
