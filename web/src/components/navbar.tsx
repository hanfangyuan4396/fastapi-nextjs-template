"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { LogOutIcon } from "lucide-react";
import { useMemo, useState } from "react";

import { cn } from "@/lib/utils";
import { LocaleSwitcher } from "./locale-switcher";
import { logout } from "@/service/auth";
import { clearAccessToken, getCurrentUserRole, Role } from "@/lib/auth";
import { useCurrentUser } from "@/lib/use-current-user";
import { ChangePasswordDialog } from "@/components/change-password-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const baseLinks = [
  { href: "/", labelKey: "nav.home" },
  { href: "/students", labelKey: "nav.students" },
];

export function Navbar() {
  const pathname = usePathname();
  const t = useTranslations();
  const router = useRouter();
  const role = getCurrentUserRole();
  const { user, loading } = useCurrentUser();
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);

  const displayName = user?.username || t("nav.userUnknown");
  const avatarText = useMemo(() => {
    if (!user?.username) return "?";
    return user.username.trim().charAt(0).toUpperCase() || "?";
  }, [user?.username]);
  const isUserLoading = loading && !user;

  // 登录页不显示导航栏
  if (pathname === "/login" || pathname?.startsWith("/login/")) {
    return null;
  }

  return (
    <header className="border-b bg-background">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="text-base sm:text-lg">{t("nav.siteName")}</span>
        </Link>

        <nav className="hidden items-center gap-6 text-sm font-medium sm:flex">
          {(role === Role.Admin ? [...baseLinks, { href: "/students-management", labelKey: "nav.studentsManagement" }] : baseLinks).map((link) => {
            const isActive = link.href === "/"
              ? pathname === "/"
              : pathname === link.href || pathname.startsWith(link.href + "/");

            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "transition-colors hover:text-primary",
                  isActive ? "text-primary" : "text-muted-foreground"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                {t(link.labelKey)}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-3">
          <LocaleSwitcher />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="flex items-center gap-3 rounded-full border border-transparent px-2 py-1 text-sm transition-colors hover:border-border hover:bg-accent/50"
                type="button"
              >
                {isUserLoading ? (
                  <div className="h-8 w-8 animate-pulse rounded-full bg-muted" aria-hidden="true" />
                ) : (
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                    {avatarText}
                  </div>
                )}
                {isUserLoading ? (
                  <span className="h-4 w-24 animate-pulse rounded bg-muted" aria-hidden="true" />
                ) : (
                  <span className="max-w-[180px] truncate text-foreground">
                    {displayName}
                  </span>
                )}
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel className="text-xs text-muted-foreground">
                {t("nav.account")}
              </DropdownMenuLabel>
              <DropdownMenuItem onSelect={() => setChangePasswordOpen(true)}>
                {t("nav.changePassword")}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onSelect={async () => {
                  try {
                    await logout();
                  } finally {
                    clearAccessToken();
                    router.replace("/login");
                  }
                }}
              >
                <LogOutIcon className="h-4 w-4" />
                {t("nav.logout")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <ChangePasswordDialog
        open={changePasswordOpen}
        onClose={() => setChangePasswordOpen(false)}
      />
    </header>
  );
}
