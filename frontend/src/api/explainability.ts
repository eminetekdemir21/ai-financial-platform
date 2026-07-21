import { apiClient } from "./client";

export interface FraudExplanation {
  transaction_id: string;
  description: string;
  amount: string;
  is_flagged: boolean;
  fraud_score: number;
  reasons: string[];
  risk_level: string;
  recommendation: string;
}

export interface HealthScoreExplanation {
  score: number;
  grade: string;
  factors: {
    name: string;
    score: number;
    weight: string;
    detail: string;
    reason: string;
  }[];
  improvement_tips: string[];
  explanation: string;
}

export async function explainFraud(accountId: string, transactionId: string): Promise<FraudExplanation> {
  const { data } = await apiClient.get(`/explain/fraud/${accountId}/${transactionId}`);
  return data;
}

export async function explainHealthScore(accountId: string): Promise<HealthScoreExplanation> {
  const { data } = await apiClient.get(`/explain/health-score/${accountId}`);
  return data;
}
