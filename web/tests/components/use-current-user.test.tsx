import { useEffect } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { useCurrentUser } from "@/lib/use-current-user";
import { getAccessToken, getAuthChangedEventName } from "@/lib/auth";
import { getMe } from "@/service/auth";

vi.mock("@/lib/auth", () => ({
  getAccessToken: vi.fn(),
  getAuthChangedEventName: vi.fn(),
}));

vi.mock("@/service/auth", () => ({
  getMe: vi.fn(),
}));

type HarnessProps = {
  onReady?: (refresh: () => Promise<void>) => void;
};

function CurrentUserHarness({ onReady }: HarnessProps) {
  const { user, loading, refresh } = useCurrentUser();

  useEffect(() => {
    onReady?.(refresh);
  }, [onReady, refresh]);

  return (
    <div>
      <span data-testid="loading">{loading ? "loading" : "done"}</span>
      <span data-testid="username">{user?.username ?? ""}</span>
    </div>
  );
}

const userAlpha = {
  id: "1",
  username: "alpha",
  role: "admin",
  is_active: true,
  token_version: 1,
};

const userBravo = {
  id: "2",
  username: "bravo",
  role: "admin",
  is_active: true,
  token_version: 1,
};

describe("useCurrentUser", () => {
  beforeEach(() => {
    vi.mocked(getAccessToken).mockReset();
    vi.mocked(getAuthChangedEventName).mockReset();
    vi.mocked(getMe).mockReset();
  });

  it("refresh() 主动刷新用户信息", async () => {
    const refreshRef: { current?: () => Promise<void> } = {};
    vi.mocked(getAccessToken).mockReturnValue("token");
    vi.mocked(getAuthChangedEventName).mockReturnValue("auth:changed");
    vi.mocked(getMe)
      .mockResolvedValueOnce({ code: 0, message: "", data: userAlpha })
      .mockResolvedValueOnce({ code: 0, message: "", data: userBravo });

    render(
      <CurrentUserHarness onReady={(refresh) => {
        refreshRef.current = refresh;
      }} />
    );

    expect(await screen.findByText("alpha")).toBeInTheDocument();

    await refreshRef.current?.();

    await waitFor(() => {
      expect(screen.getByText("bravo")).toBeInTheDocument();
    });
  });

  it("auth:changed 事件触发刷新", async () => {
    vi.mocked(getAccessToken).mockReturnValue("token");
    vi.mocked(getAuthChangedEventName).mockReturnValue("auth:changed");
    vi.mocked(getMe)
      .mockResolvedValueOnce({ code: 0, message: "", data: userAlpha })
      .mockResolvedValueOnce({ code: 0, message: "", data: userBravo });

    render(<CurrentUserHarness />);

    expect(await screen.findByText("alpha")).toBeInTheDocument();

    window.dispatchEvent(new Event("auth:changed"));

    await waitFor(() => {
      expect(screen.getByText("bravo")).toBeInTheDocument();
    });
  });
});
