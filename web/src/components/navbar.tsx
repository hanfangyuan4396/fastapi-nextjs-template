"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";

import { cn } from "@/lib/utils";
import { LocaleSwitcher } from "./locale-switcher";

const links = [
  { href: "/", labelKey: "nav.home" },
  { href: "/students", labelKey: "nav.students" },
];

export function Navbar() {
  const pathname = usePathname();
  const t = useTranslations();

  return (
    <header className="border-b bg-background">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="text-base sm:text-lg">{t("nav.siteName")}</span>
        </Link>

        <nav className="hidden items-center gap-6 text-sm font-medium sm:flex">
          {links.map((link) => {
            const isActive = link.href === "/"
              ? pathname === "/"
              : pathname.startsWith(link.href);

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
        </div>
      </div>
    </header>
  );
}
