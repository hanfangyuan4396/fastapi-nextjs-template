export type AccessToken = string | null;

let currentAccessToken: AccessToken = null;

export function setAccessToken(token: string): void {
  currentAccessToken = token;
}

export function getAccessToken(): AccessToken {
  return currentAccessToken;
}

export function clearAccessToken(): void {
  currentAccessToken = null;
}
