import { apiClient } from "./client";

export interface HealthScoreFactor {
  score: number;
  weight: number;
  comment: string;
  label: string;
}

export interface HealthScoreResult {
  score: number;
  grade: string;
  breakdown: Record<string, HealthScoreFactor>;
  summary: string;
}

export async function getHealthScore(accountId: string): Promise<HealthScoreResult> {
  const response = await apiClient.get<HealthScoreResult>(`/health-score/${accountId}`);
  return response.data;
}
