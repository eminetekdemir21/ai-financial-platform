import { apiClient } from "./client";

export interface Transaction {
  id: string;
  account_id: string;
  amount: string;
  description: string;
  merchant: string | null;
  transaction_date: string;
  category: string | null;
  fraud_score: number | null;
  is_flagged: boolean;
  source: string;
}

export interface UploadResult {
  imported_count: number;
  source: string;
  categorized_count?: number;
  skipped_duplicates?: number;
}

export interface CategorizationRunResult {
  total_categorized: number;
  by_method: { rule: number; embedding: number; fallback: number };
}

export interface FraudRunResult {
  total_analyzed: number;
  flagged_count: number;
}

export async function listTransactions(accountId: string): Promise<Transaction[]> {
  const response = await apiClient.get<Transaction[]>("/transactions/list", {
    params: { account_id: accountId },
  });
  return response.data;
}

export async function uploadCsv(accountId: string, file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiClient.post<UploadResult>(
    "/transactions/upload/csv",
    formData,
    {
      params: { account_id: accountId },
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return response.data;
}

export async function runCategorization(
  accountId: string
): Promise<CategorizationRunResult> {
  const response = await apiClient.post<CategorizationRunResult>(
    "/categorization/run",
    null,
    { params: { account_id: accountId } }
  );
  return response.data;
}

export async function runFraudDetection(accountId: string): Promise<FraudRunResult> {
  const response = await apiClient.post<FraudRunResult>("/fraud/run", null, {
    params: { account_id: accountId },
  });
  return response.data;
}
