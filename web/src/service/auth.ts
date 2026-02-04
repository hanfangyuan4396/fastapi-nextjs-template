import { httpGet, httpPost, type ApiResponse } from "./http";

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

export type UserProfile = {
  id: string;
  username: string;
  role: string;
  is_active: boolean;
  token_version: number;
};

export type MeResponse = ApiResponse<UserProfile>;

export async function getMe(): Promise<MeResponse> {
  return httpGet<UserProfile>("/auth/me", undefined, { credentials: "include" });
}

export type LogoutResponse = ApiResponse<null>;

export async function logout(): Promise<LogoutResponse> {
  return httpPost<null>("/auth/logout", undefined, { credentials: "include" });
}

// ===== Password =====

export type ChangePasswordPayload = {
  old_password: string;
  new_password: string;
  confirm_password: string;
};

export type ChangePasswordResponse = ApiResponse<null>;

export async function changePassword(
  payload: ChangePasswordPayload
): Promise<ChangePasswordResponse> {
  return httpPost<null>("/auth/password/change", payload, { credentials: "include" });
}

export type SendResetCodePayload = {
  email: string;
};

export type SendResetCodeResponse = ApiResponse<null>;

export async function sendResetCode(
  payload: SendResetCodePayload
): Promise<SendResetCodeResponse> {
  return httpPost<null>("/auth/password/reset/send-code", payload, { credentials: "include" });
}

export type ResetPasswordPayload = {
  email: string;
  code: string;
  new_password: string;
  confirm_password: string;
};

export type ResetPasswordResponse = ApiResponse<null>;

export async function resetPassword(
  payload: ResetPasswordPayload
): Promise<ResetPasswordResponse> {
  return httpPost<null>("/auth/password/reset/confirm", payload, { credentials: "include" });
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
