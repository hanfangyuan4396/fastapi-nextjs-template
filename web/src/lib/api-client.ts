export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(message: string, status: number, body?: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

export type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
  // 允许后端扩展其他字段
  [key: string]: unknown;
};

interface MessageBody {
  message?: string;
}

function getErrorMessageFromBody(body: unknown): string {
  if (body && typeof body === "object" && "message" in body) {
    const msg = (body as MessageBody).message;
    if (typeof msg === "string" && msg.trim().length > 0) {
      return msg;
    }
  }
  return "Request failed";
}

/**
 * 统一 fetch 包装：
 * - 非 2xx 抛出 ApiError，错误文案取自响应体的 message 字段
 * - 2xx 返回 JSON：
 *   - 若符合 {code,message,data} 结构，则返回 data
 *   - 否则直接返回解析后的 JSON
 */
export async function apiFetch<T>(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(input, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  const contentType = response.headers.get("content-type");
  const isJson = contentType?.includes("application/json");
  const body = isJson ? await response.json().catch(() => undefined) : undefined;

  if (!response.ok) {
    const message = getErrorMessageFromBody(body);
    throw new ApiError(message, response.status, body);
  }

  // 优先适配统一响应结构 code/message/data
  if (body && typeof body === "object") {
    const obj = body as Partial<ApiResponse<T>>;
    if (
      Object.prototype.hasOwnProperty.call(obj, "code") &&
      Object.prototype.hasOwnProperty.call(obj, "message") &&
      Object.prototype.hasOwnProperty.call(obj, "data")
    ) {
      return obj.data as T;
    }
  }

  // 否则直接返回解析后的 JSON（或 undefined）
  return body as T;
}
