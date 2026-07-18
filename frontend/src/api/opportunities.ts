import { apiClient } from "./client";

export interface Opportunity {
  type: string;
  title: string;
  description: string;
  monthly_saving: string;
  annual_saving: string;
  priority: string;
  category: string;
  action: string;
}

export interface OpportunityReport {
  opportunity_score: number;
  total_monthly_saving: string;
  total_annual_saving: string;
  opportunities: Opportunity[];
  summary: string;
  subscriptions_total: string;
  top_merchant_waste: { merchant: string; monthly: number }[];
}

export async function getOpportunities(accountId: string): Promise<OpportunityReport> {
  const { data } = await apiClient.get(`/opportunities/${accountId}`);
  return data;
}
