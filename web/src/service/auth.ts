import { httpPost, type ApiResponse } from "./http";

export type LoginPayload = {
  username: string;
  password: string;
};

export type LoginData = {
  access_token: string;
  refresh_expires_at?: number;
};

export type LoginResponse = ApiResponse<LoginData>;

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  return httpPost<LoginData>("/auth/login", payload, { credentials: "include" });
}

export type LogoutResponse = ApiResponse<null>;

export async function logout(): Promise<LogoutResponse> {
  return httpPost<null>("/auth/logout", undefined, { credentials: "include" });
}
