import { beforeEach, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";

import { server } from "../msw/server";
import { listStudents } from "@/service/students";
import { clearAccessToken, getAccessToken } from "@/lib/auth";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost/api";

describe("students integration", () => {
  beforeEach(() => {
    clearAccessToken();
  });

  it("refreshes token and retries listStudents", async () => {
    let callCount = 0;
    let lastUrl: URL | null = null;

    server.use(
      http.get(`${baseUrl}/students`, ({ request }) => {
        callCount += 1;
        lastUrl = new URL(request.url);
        const auth = request.headers.get("authorization");
        if (auth !== "Bearer test-token") {
          return new HttpResponse(null, { status: 401 });
        }
        return HttpResponse.json({
          code: 0,
          message: "",
          data: { items: [], page: 2, page_size: 10, total: 0 },
        });
      })
    );

    const res = await listStudents({ page: 2, page_size: 10 });

    expect(callCount).toBe(2);
    expect(lastUrl?.searchParams.get("page")).toBe("2");
    expect(lastUrl?.searchParams.get("page_size")).toBe("10");
    expect(getAccessToken()).toBe("test-token");
    expect(res.code).toBe(0);
  });
});
