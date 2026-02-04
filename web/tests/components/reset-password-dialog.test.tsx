import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ResetPasswordDialog } from "@/app/login/components/reset-password-dialog";
import { resetPassword, sendResetCode } from "@/service/auth";
import { renderWithIntl } from "../utils/render";

vi.mock("@/service/auth", () => ({
  resetPassword: vi.fn(),
  sendResetCode: vi.fn(),
}));

vi.mock("@/lib/withToast", () => ({
  withToast: (p: Promise<unknown>) => p,
}));

describe("ResetPasswordDialog", () => {
  it("submits reset password when form is valid", async () => {
    vi.mocked(resetPassword).mockResolvedValue({ code: 0, message: "", data: null });
    vi.mocked(sendResetCode).mockResolvedValue({ code: 0, message: "", data: null });
    const user = userEvent.setup();

    renderWithIntl(<ResetPasswordDialog open onClose={vi.fn()} />);

    await user.type(screen.getByLabelText("邮箱"), "reset@example.com");
    await user.type(screen.getByLabelText("验证码"), "123456");
    await user.type(screen.getByLabelText("新密码"), "newpass1");
    await user.type(screen.getByLabelText("确认新密码"), "newpass1");
    await user.click(screen.getByRole("button", { name: "重置密码" }));

    expect(resetPassword).toHaveBeenCalledWith({
      email: "reset@example.com",
      code: "123456",
      new_password: "newpass1",
      confirm_password: "newpass1",
    });
  });
});
