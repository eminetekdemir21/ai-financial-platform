import { apiClient } from "./client";

export interface SimulationRequest {
  income_change?: number;
  category_changes?: Record<string, number>;
  one_time_expense?: number;
  description?: string;
  horizon_months?: number;
}

export interface MonthlyProjection {
  month: number;
  income: string;
  expense: string;
  net_savings: string;
  cumulative_savings: string;
}

export interface SimulationResult {
  description: string;
  current_monthly_income: string;
  current_monthly_expense: string;
  current_monthly_savings: string;
  simulated_monthly_income: string;
  simulated_monthly_expense: string;
  simulated_monthly_savings: string;
  savings_difference: string;
  annual_savings_difference: string;
  horizon_months: number;
  monthly_projections: MonthlyProjection[];
  ai_summary: string;
  impact_level: string;
}

export interface SavedScenarioSummary {
  id: string;
  name: string;
  impact_level: string;
  savings_difference: string;
  annual_savings_difference: string;
  horizon_months: number;
  created_at: string;
}

export interface SavedScenarioDetail {
  id: string;
  name: string;
  created_at: string;
  request: SimulationRequest;
  result: SimulationResult;
}

export async function runSimulation(
  accountId: string,
  payload: SimulationRequest
): Promise<SimulationResult> {
  const response = await apiClient.post<SimulationResult>(
    `/simulation/${accountId}`,
    payload
  );
  return response.data;
}

export async function saveScenario(
  accountId: string,
  name: string,
  payload: SimulationRequest
): Promise<SavedScenarioDetail> {
  const response = await apiClient.post<SavedScenarioDetail>(
    `/simulation/${accountId}/scenarios`,
    { name, request: payload }
  );
  return response.data;
}

export async function listScenarios(
  accountId: string
): Promise<SavedScenarioSummary[]> {
  const response = await apiClient.get<SavedScenarioSummary[]>(
    `/simulation/${accountId}/scenarios`
  );
  return response.data;
}

export async function getScenario(
  accountId: string,
  scenarioId: string
): Promise<SavedScenarioDetail> {
  const response = await apiClient.get<SavedScenarioDetail>(
    `/simulation/${accountId}/scenarios/${scenarioId}`
  );
  return response.data;
}

export async function deleteScenario(
  accountId: string,
  scenarioId: string
): Promise<void> {
  await apiClient.delete(`/simulation/${accountId}/scenarios/${scenarioId}`);
}
