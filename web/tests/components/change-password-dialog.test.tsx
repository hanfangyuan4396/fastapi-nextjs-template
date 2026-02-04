import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ChangePasswordDialog } from "@/components/change-password-dialog";
import { changePassword } from "@/service/auth";
import { renderWithIntl } from "../utils/render";

vi.mock("@/service/auth", () => ({
  changePassword: vi.fn(),
}));

vi.mock("@/lib/withToast", () => ({
  withToast: (p: Promise<unknown>) => p,
}));

describe("ChangePasswordDialog", () => {
  it("submits change password when form is valid", async () => {
    vi.mocked(changePassword).mockResolvedValue({ code: 0, message: "", data: null });
    const user = userEvent.setup();
    const onClose = vi.fn();

    renderWithIntl(<ChangePasswordDialog open onClose={onClose} />);

    await user.type(screen.getByLabelText("旧密码"), "oldpass");
    await user.type(screen.getByLabelText("新密码"), "newpass1");
    await user.type(screen.getByLabelText("确认新密码"), "newpass1");
    await user.click(screen.getByRole("button", { name: "保存修改" }));

    expect(changePassword).toHaveBeenCalledWith({
      old_password: "oldpass",
      new_password: "newpass1",
      confirm_password: "newpass1",
    });
  });
});
