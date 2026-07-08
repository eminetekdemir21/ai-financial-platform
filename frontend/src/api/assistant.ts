import { apiClient } from "./client";

export interface ChatResponse {
  reply: string;
}

export async function sendChatMessage(
  accountId: string,
  message: string
): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>("/assistant/chat", {
    account_id: accountId,
    message,
  });
  return response.data;
}
