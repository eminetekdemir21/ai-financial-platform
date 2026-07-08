import { apiClient } from "./client";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login", {
    email,
    password,
  });
  return response.data;
}

export async function register(
  email: string,
  password: string,
  full_name: string
): Promise<User> {
  const response = await apiClient.post<User>("/auth/register", {
    email,
    password,
    full_name,
  });
  return response.data;
}

export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me");
  return response.data;
}
