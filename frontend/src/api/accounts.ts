import { apiClient } from "./client";

export interface Account {
  id: string;
  bank_name: string;
  account_number_masked: string;
  currency: string;
  current_balance: string;
}

export interface CreateAccountPayload {
  bank_name: string;
  account_number_masked: string;
}

export async function listAccounts(): Promise<Account[]> {
  const response = await apiClient.get<Account[]>("/transactions/accounts");
  return response.data;
}

export async function createAccount(payload: CreateAccountPayload): Promise<Account> {
  const response = await apiClient.post<Account>("/transactions/accounts", payload);
  return response.data;
}

export async function deleteAccount(accountId: string): Promise<void> {
  await apiClient.delete(`/transactions/accounts/${accountId}`);
}
