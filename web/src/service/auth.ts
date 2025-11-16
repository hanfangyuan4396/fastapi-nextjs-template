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

// ===== Registration (email + OTP) =====

export type SendRegisterCodePayload = {
  email: string;
};

export type SendRegisterCodeResponse = ApiResponse<null>;

export async function sendRegisterCode(
  payload: SendRegisterCodePayload
): Promise<SendRegisterCodeResponse> {
  return httpPost<null>("/auth/register/send-code", payload, { credentials: "include" });
}

export type VerifyAndCreatePayload = {
  email: string;
  code: string;
  password: string;
};

export type VerifyAndCreateData = {
  access_token: string;
  refresh_expires_at?: number;
};

export type VerifyAndCreateResponse = ApiResponse<VerifyAndCreateData>;

export async function verifyAndCreate(
  payload: VerifyAndCreatePayload
): Promise<VerifyAndCreateResponse> {
  return httpPost<VerifyAndCreateData>("/auth/register/verify-and-create", payload, {
    credentials: "include",
  });
}
