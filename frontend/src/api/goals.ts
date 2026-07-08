import { apiClient } from "./client";

export interface Goal {
  id: string;
  account_id: string;
  name: string;
  target_amount: string;
  target_date: string;
  priority: string;
  current_savings: string;
  notes: string | null;
  status: string;
}

export interface SavingOpportunity {
  category: string;
  monthly_spend: number;
  saving_10_percent: number;
  saving_20_percent: number;
  days_earlier: number;
}

export interface GoalAnalysis {
  goal: Goal;
  months_remaining: number;
  monthly_savings_needed: string;
  current_monthly_savings: string;
  is_achievable: boolean;
  estimated_completion_date: string;
  shortfall_per_month: string;
  top_saving_opportunities: SavingOpportunity[];
  ai_recommendation: string;
}

export interface GoalCreate {
  name: string;
  target_amount: number;
  target_date: string;
  priority: string;
  current_savings: number;
  notes?: string;
}

export async function createGoal(accountId: string, data: GoalCreate): Promise<Goal> {
  const { data: res } = await apiClient.post(`/goals/${accountId}`, data);
  return res;
}

export async function listGoals(accountId: string): Promise<Goal[]> {
  const { data } = await apiClient.get(`/goals/${accountId}`);
  return data;
}

export async function analyzeGoal(goalId: string, accountId: string): Promise<GoalAnalysis> {
  const { data } = await apiClient.get(`/goals/analyze/${goalId}`, {
    params: { account_id: accountId },
  });
  return data;
}

export async function deleteGoal(goalId: string): Promise<void> {
  await apiClient.delete(`/goals/${goalId}`);
}

