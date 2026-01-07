import { beforeEach, describe, expect, it } from "vitest";

import {
  clearAccessToken,
  getAccessToken,
  getCurrentUserRole,
  Role,
  setAccessToken,
} from "@/lib/auth";

function base64UrlEncode(input: string): string {
  return Buffer.from(input)
    .toString("base64")
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
}

function buildToken(payload: Record<string, unknown>): string {
  const header = base64UrlEncode(JSON.stringify({ alg: "none", typ: "JWT" }));
  const body = base64UrlEncode(JSON.stringify(payload));
  return `${header}.${body}.sig`;
}

describe("auth tokens", () => {
  beforeEach(() => {
    clearAccessToken();
  });

  it("stores token and parses admin role", () => {
    const token = buildToken({ role: "admin" });
    setAccessToken(token);

    expect(getAccessToken()).toBe(token);
    expect(getCurrentUserRole()).toBe(Role.Admin);
  });

  it("clears token and role", () => {
    setAccessToken(buildToken({ role: "admin" }));
    clearAccessToken();

    expect(getAccessToken()).toBeNull();
    expect(getCurrentUserRole()).toBeNull();
  });

  it("handles invalid token payloads", () => {
    setAccessToken("not-a-jwt");

    expect(getAccessToken()).toBe("not-a-jwt");
    expect(getCurrentUserRole()).toBeNull();
  });
});
