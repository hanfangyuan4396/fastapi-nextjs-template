import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import { RequireRole } from "@/components/require-role";
import { Role, getCurrentUserRole } from "@/lib/auth";
import { renderWithIntl } from "../utils/render";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
}));

vi.mock("@/lib/auth", async () => {
  const actual = await vi.importActual<typeof import("@/lib/auth")>("@/lib/auth");
  return {
    ...actual,
    getCurrentUserRole: vi.fn(),
  };
});

describe("RequireRole", () => {
  it("renders children when role matches", () => {
    vi.mocked(getCurrentUserRole).mockReturnValue(Role.Admin);
    renderWithIntl(
      <RequireRole required={Role.Admin}>
        <span>allowed</span>
      </RequireRole>
    );

    expect(screen.getByText("allowed")).toBeInTheDocument();
  });

  it("redirects when role mismatches", async () => {
    vi.mocked(getCurrentUserRole).mockReturnValue("user" as unknown as Role);
    renderWithIntl(
      <RequireRole required={Role.Admin}>
        <span>denied</span>
      </RequireRole>
    );

    expect(screen.queryByText("denied")).not.toBeInTheDocument();
    await waitFor(() => {
      expect(replace).toHaveBeenCalledWith("/");
    });
  });
});
