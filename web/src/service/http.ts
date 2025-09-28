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

export async function httpGet<T>(
  path: string,
  params?: Record<string, unknown>,
  init?: FetchInit
): Promise<ApiResponse<T>> {
  const url = joinUrl(API_BASE_URL, path) + buildQuery(params);
  const res = await fetch(url, {
    ...init,
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers as Record<string, string> | undefined),
    },
  });
  const json = (await res.json()) as ApiResponse<T>;
  return json;
}

export async function httpPost<T>(
  path: string,
  body?: unknown,
  init?: FetchInit
): Promise<ApiResponse<T>> {
  const url = joinUrl(API_BASE_URL, path);
  const res = await fetch(url, {
    ...init,
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers as Record<string, string> | undefined),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const json = (await res.json()) as ApiResponse<T>;
  return json;
}
