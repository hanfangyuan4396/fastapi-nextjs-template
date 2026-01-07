import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { RequireAuth } from "@/components/require-auth";
import { getAccessToken, setAccessToken } from "@/lib/auth";
import { httpPost } from "@/service/http";

let mockPathname = "/students";
const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => mockPathname,
}));

vi.mock("@/lib/auth", () => ({
  getAccessToken: vi.fn(),
  setAccessToken: vi.fn(),
}));

vi.mock("@/service/http", () => ({
  httpPost: vi.fn(),
}));

describe("RequireAuth", () => {
  beforeEach(() => {
    mockPathname = "/students";
    replace.mockClear();
    vi.mocked(getAccessToken).mockReset();
    vi.mocked(setAccessToken).mockReset();
    vi.mocked(httpPost).mockReset();
  });

  it("renders children when access token exists", async () => {
    vi.mocked(getAccessToken).mockReturnValue("token");
    render(
      <RequireAuth>
        <span>ok</span>
      </RequireAuth>
    );

    expect(await screen.findByText("ok")).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("refreshes token and renders children", async () => {
    vi.mocked(getAccessToken).mockReturnValue(null);
    vi.mocked(httpPost).mockResolvedValue({
      code: 0,
      message: "",
      data: { access_token: "new-token" },
    });

    render(
      <RequireAuth>
        <span>ready</span>
      </RequireAuth>
    );

    expect(await screen.findByText("ready")).toBeInTheDocument();
    expect(setAccessToken).toHaveBeenCalledWith("new-token");
    expect(replace).not.toHaveBeenCalled();
  });

  it("redirects to login when refresh fails", async () => {
    vi.mocked(getAccessToken).mockReturnValue(null);
    vi.mocked(httpPost).mockRejectedValue(new Error("network"));

    render(
      <RequireAuth>
        <span>protected</span>
      </RequireAuth>
    );

    await waitFor(() => {
      expect(replace).toHaveBeenCalledWith("/login?next=%2Fstudents");
    });
    expect(screen.queryByText("protected")).not.toBeInTheDocument();
  });
});
