import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  login,
  logout,
  sendRegisterCode,
  verifyAndCreate,
} from "@/service/auth";
import { httpPost } from "@/service/http";

vi.mock("@/service/http", () => ({
  httpPost: vi.fn(),
}));

describe("auth service", () => {
  beforeEach(() => {
    vi.mocked(httpPost).mockReset();
    vi.mocked(httpPost).mockResolvedValue({ code: 0, message: "", data: null });
  });

  it("calls login with credentials", async () => {
    await login({ username: "user", password: "pass" });

    expect(httpPost).toHaveBeenCalledWith(
      "/auth/login",
      { username: "user", password: "pass" },
      { credentials: "include" }
    );
  });

  it("calls logout with credentials", async () => {
    await logout();

    expect(httpPost).toHaveBeenCalledWith(
      "/auth/logout",
      undefined,
      { credentials: "include" }
    );
  });

  it("calls sendRegisterCode with credentials", async () => {
    await sendRegisterCode({ email: "test@example.com" });

    expect(httpPost).toHaveBeenCalledWith(
      "/auth/register/send-code",
      { email: "test@example.com" },
      { credentials: "include" }
    );
  });

  it("calls verifyAndCreate with credentials", async () => {
    await verifyAndCreate({ email: "test@example.com", code: "1234", password: "secret" });

    expect(httpPost).toHaveBeenCalledWith(
      "/auth/register/verify-and-create",
      { email: "test@example.com", code: "1234", password: "secret" },
      { credentials: "include" }
    );
  });
});
