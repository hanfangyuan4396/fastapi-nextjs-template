export type AccessToken = string | null;
export enum Role {
  Admin = "admin",
}
export type UserRole = Role | null;

const STORAGE_ACCESS_TOKEN_KEY = "access_token";

let currentAccessToken: AccessToken = null;
let currentUserRole: UserRole = null;

function isBrowser(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function base64UrlDecode(input: string): string {
  try {
    const pad = (s: string) => s + "=".repeat((4 - (s.length % 4)) % 4);
    const base64 = pad(input.replace(/-/g, "+").replace(/_/g, "/"));
    if (typeof window !== "undefined" && typeof window.atob === "function") {
      return decodeURIComponent(
        Array.prototype.map
          .call(window.atob(base64), (c: string) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
          .join("")
      );
    }
    // Node.js fallback
    return Buffer.from(base64, "base64").toString("utf-8");
  } catch {
    return "";
  }
}

function extractRoleFromJwt(token: string): Role | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payloadJson = base64UrlDecode(parts[1]);
    if (!payloadJson) return null;
    const payload = JSON.parse(payloadJson) as { role?: unknown };
    const roleVal = payload.role;
    if (typeof roleVal === "string" && roleVal.length > 0) {
      switch (roleVal) {
        case Role.Admin:
          return Role.Admin;
        default:
          return null;
      }
    }
    return null;
  } catch {
    return null;
  }
}

export function setAccessToken(token: string): void {
  currentAccessToken = token;
  currentUserRole = extractRoleFromJwt(token);
  if (isBrowser()) {
    try {
      window.localStorage.setItem(STORAGE_ACCESS_TOKEN_KEY, token);
    } catch {
      // 忽略存储失败
    }
  }
}

export function getAccessToken(): AccessToken {
  if (!currentAccessToken && isBrowser()) {
    try {
      const stored = window.localStorage.getItem(STORAGE_ACCESS_TOKEN_KEY);
      if (stored) {
        currentAccessToken = stored;
        currentUserRole = extractRoleFromJwt(stored);
      }
    } catch {
      // 忽略读取失败
    }
  }
  return currentAccessToken;
}

export function getCurrentUserRole(): UserRole {
  return currentUserRole;
}

export function isAdmin(): boolean {
  return currentUserRole === Role.Admin;
}

export function clearAccessToken(): void {
  currentAccessToken = null;
  currentUserRole = null;
  if (isBrowser()) {
    try {
      window.localStorage.removeItem(STORAGE_ACCESS_TOKEN_KEY);
    } catch {
      // 忽略清理失败
    }
  }
}
