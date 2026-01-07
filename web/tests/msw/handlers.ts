import { http, HttpResponse, type HttpHandler } from "msw";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost/api";

export const handlers: HttpHandler[] = [
  http.post(`${baseUrl}/auth/refresh`, () =>
    HttpResponse.json({ code: 0, message: "", data: { access_token: "test-token" } })
  ),
];
