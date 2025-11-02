export type ApiResponse<T> = {
  code: number;
  message: string;
  data?: T | null;
};

export const API_BASE_URL: string =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

function ensureLeadingSlash(path: string): string {
  if (!path) return "/";
  return path.startsWith("/") ? path : `/${path}`;
}

function joinUrl(base: string, path: string): string {
  const normalizedBase = base.replace(/\/$/, "");
  const normalizedPath = ensureLeadingSlash(path);
  return `${normalizedBase}${normalizedPath}`;
}

function buildQuery(params?: Record<string, unknown>): string {
  if (!params) return "";
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    usp.append(key, String(value));
  });
  const qs = usp.toString();
  return qs ? `?${qs}` : "";
}

type NextFetchOptions = { revalidate?: number | false; tags?: string[] };
type FetchInit = RequestInit & { next?: NextFetchOptions; cache?: RequestCache };

import { getAccessToken, setAccessToken, clearAccessToken } from "@/lib/auth";

function buildAuthHeaders(init?: FetchInit): Record<string, string> {
  const base = (init?.headers as Record<string, string> | undefined) || {};
  const token = getAccessToken();
  if (token) {
    return { ...base, Authorization: `Bearer ${token}` };
  }
  return base;
}

let refreshPromise: Promise<boolean> | null = null;

function isAuthPath(path: string): boolean {
  return path.startsWith("/auth/");
}

async function performRefresh(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
      const url = joinUrl(API_BASE_URL, "/auth/refresh");
      const res = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });
      // 刷新接口总是 200，依据业务 code 判断
      const json = (await res.json()) as ApiResponse<{ access_token?: string | null }>;
      if (json && json.code === 0 && json.data?.access_token) {
        setAccessToken(json.data.access_token);
        return true;
      }
      return false;
    } catch {
      return false;
    } finally {
      // 下一个刷新可再次触发
      const p = refreshPromise;
      refreshPromise = null;
      void p; // 避免未使用变量告警
    }
  })();
  return refreshPromise;
}

async function requestWithAutoRefresh<T>(
  method: "GET" | "POST",
  path: string,
  init?: FetchInit,
  body?: unknown,
  params?: Record<string, unknown>
): Promise<ApiResponse<T>> {
  const url = joinUrl(API_BASE_URL, path) + (method === "GET" ? buildQuery(params) : "");

  const buildInit = (): FetchInit => ({
    ...init,
    method,
    credentials: init?.credentials ?? "include",
    headers: {
      "Content-Type": "application/json",
      ...buildAuthHeaders(init),
    },
    body: method === "POST" ? (body === undefined ? undefined : JSON.stringify(body)) : undefined,
  });

  let res = await fetch(url, buildInit());

  if (res.status === 401 && !isAuthPath(path)) {
    const ok = await performRefresh();
    if (ok) {
      // 令牌已更新，重放请求
      res = await fetch(url, buildInit());
    } else {
      // 刷新失败：清理并跳登录
      clearAccessToken();
      if (typeof window !== "undefined") {
        const loginUrl = "/login";
        try {
          window.location.replace(loginUrl);
        } catch {
          window.location.href = loginUrl;
        }
      }
      return { code: 40100, message: "unauthorized", data: null } as ApiResponse<T>;
    }
  }

  // 正常解析响应体（期望统一为 ApiResponse<T>）
  try {
    const json = (await res.json()) as ApiResponse<T>;
    return json;
  } catch {
    // 非 JSON 响应的兜底
    return { code: res.ok ? 0 : res.status, message: res.statusText, data: null } as ApiResponse<T>;
  }
}

export async function httpGet<T>(
  path: string,
  params?: Record<string, unknown>,
  init?: FetchInit
): Promise<ApiResponse<T>> {
  return requestWithAutoRefresh<T>("GET", path, init, undefined, params);
}

export async function httpPost<T>(
  path: string,
  body?: unknown,
  init?: FetchInit
): Promise<ApiResponse<T>> {
  return requestWithAutoRefresh<T>("POST", path, init, body);
}
