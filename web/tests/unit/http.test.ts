import { beforeEach, describe, expect, it, vi } from "vitest";

import { httpGet } from "@/service/http";
import { clearAccessToken, getAccessToken, setAccessToken } from "@/lib/auth";

let token: string | null = null;

vi.mock("@/lib/auth", () => ({
  getAccessToken: vi.fn(() => token),
  setAccessToken: vi.fn((next: string) => {
    token = next;
  }),
  clearAccessToken: vi.fn(() => {
    token = null;
  }),
}));

function mockJsonResponse(body: unknown, status = 200) {
  return {
    status,
    ok: status >= 200 && status < 300,
    statusText: status === 200 ? "OK" : "Error",
    json: async () => body,
  };
}

describe("httpGet", () => {
  beforeEach(() => {
    token = null;
    vi.mocked(clearAccessToken).mockClear();
    vi.mocked(setAccessToken).mockClear();
    vi.mocked(getAccessToken).mockClear();
    vi.stubGlobal("fetch", vi.fn());
  });

  it("builds query params and attaches auth header", async () => {
    token = "abc";
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValue(
      mockJsonResponse({ code: 0, message: "", data: { ok: true } })
    );

    const res = await httpGet<{ ok: boolean }>("/students", {
      page: 1,
      page_size: 20,
      unused: undefined,
    });

    expect(res.code).toBe(0);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/students?page=1&page_size=20");
    expect((init?.headers as Record<string, string>).Authorization).toBe("Bearer abc");
  });

  it("refreshes token after 401 and retries", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(mockJsonResponse({}, 401))
      .mockResolvedValueOnce(
        mockJsonResponse({ code: 0, message: "", data: { access_token: "test-token" } })
      )
      .mockResolvedValueOnce(
        mockJsonResponse({ code: 0, message: "", data: { items: [], page: 1 } })
      );

    const res = await httpGet("/students");

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(vi.mocked(setAccessToken)).toHaveBeenCalledWith("test-token");
    expect(res.code).toBe(0);
  });
});
