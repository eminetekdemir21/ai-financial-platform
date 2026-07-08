import { apiClient } from "./client";

export interface ForecastResult {
  method: string;
  confidence: string;
  predicted_next_month_net: number;
  current_balance_estimate: number;
  projected_balance: number;
  monthly_history: Record<string, number>;
  message: string;
}

export async function getForecast(accountId: string): Promise<ForecastResult> {
  const response = await apiClient.get<ForecastResult>(`/forecast/${accountId}`);
  return response.data;
}
