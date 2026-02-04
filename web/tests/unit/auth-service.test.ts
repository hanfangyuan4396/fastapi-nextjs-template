import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  changePassword,
  getMe,
  login,
  logout,
  resetPassword,
  sendRegisterCode,
  sendResetCode,
  verifyAndCreate,
} from "@/service/auth";
import { httpGet, httpPost } from "@/service/http";

vi.mock("@/service/http", () => ({
  httpGet: vi.fn(),
  httpPost: vi.fn(),
}));

describe("auth service", () => {
  beforeEach(() => {
    vi.mocked(httpGet).mockReset();
    vi.mocked(httpPost).mockReset();
    vi.mocked(httpGet).mockResolvedValue({ code: 0, message: "", data: null });
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

  it("calls getMe with credentials", async () => {
    await getMe();

    expect(httpGet).toHaveBeenCalledWith(
      "/auth/me",
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

  it("calls changePassword with credentials", async () => {
    await changePassword({
      old_password: "old",
      new_password: "newpass1",
      confirm_password: "newpass1",
    });

    expect(httpPost).toHaveBeenCalledWith(
      "/auth/password/change",
      { old_password: "old", new_password: "newpass1", confirm_password: "newpass1" },
      { credentials: "include" }
    );
  });

  it("calls sendResetCode with credentials", async () => {
    await sendResetCode({ email: "reset@example.com" });

    expect(httpPost).toHaveBeenCalledWith(
      "/auth/password/reset/send-code",
      { email: "reset@example.com" },
      { credentials: "include" }
    );
  });

  it("calls resetPassword with credentials", async () => {
    await resetPassword({
      email: "reset@example.com",
      code: "123456",
      new_password: "newpass1",
      confirm_password: "newpass1",
    });

    expect(httpPost).toHaveBeenCalledWith(
      "/auth/password/reset/confirm",
      {
        email: "reset@example.com",
        code: "123456",
        new_password: "newpass1",
        confirm_password: "newpass1",
      },
      { credentials: "include" }
    );
  });
});
