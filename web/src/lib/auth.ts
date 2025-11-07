export type AccessToken = string | null;
export type UserRole = string | null;

let currentAccessToken: AccessToken = null;
let currentUserRole: UserRole = null;

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

function extractRoleFromJwt(token: string): string | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payloadJson = base64UrlDecode(parts[1]);
    if (!payloadJson) return null;
    const payload = JSON.parse(payloadJson) as { role?: unknown };
    const roleVal = payload.role;
    return typeof roleVal === "string" && roleVal.length > 0 ? roleVal : null;
  } catch {
    return null;
  }
}

export function setAccessToken(token: string): void {
  currentAccessToken = token;
  currentUserRole = extractRoleFromJwt(token);
}

export function getAccessToken(): AccessToken {
  return currentAccessToken;
}

export function getCurrentUserRole(): UserRole {
  return currentUserRole;
}

export function isAdmin(): boolean {
  return currentUserRole === "admin";
}

export function clearAccessToken(): void {
  currentAccessToken = null;
  currentUserRole = null;
}
