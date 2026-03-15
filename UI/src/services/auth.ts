import { httpClient } from "./http";
import type { LoginPayload, RegisterPayload, TokenResponse, User } from "../types/api";

export async function registerUser(payload: RegisterPayload): Promise<User> {
  const response = await httpClient.post<User>("/api/v1/auth/register", payload);
  return response.data;
}

export async function loginUser(payload: LoginPayload): Promise<TokenResponse> {
  const response = await httpClient.post<TokenResponse>("/api/v1/auth/login", payload);
  return response.data;
}

export async function fetchCurrentUser(): Promise<User> {
  const response = await httpClient.get<User>("/api/v1/auth/me");
  return response.data;
}
