"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "首页" },
  { href: "/students", label: "学生管理" },
];

type Locale = "zh" | "en";

export function Navbar() {
  const pathname = usePathname();
  const [locale, setLocale] = useState<Locale>(() => {
    if (typeof window === "undefined") {
      return "zh";
    }

    const saved = window.localStorage.getItem("preferred-locale");

    return saved === "en" ? "en" : "zh";
  });

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    window.localStorage.setItem("preferred-locale", locale);
    document.documentElement.lang = locale;
  }, [locale]);

  const handleToggle = () => {
    setLocale((prev) => (prev === "zh" ? "en" : "zh"));
  };

  return (
    <header className="border-b bg-background">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="text-base sm:text-lg">Student Manager</span>
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
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            className="font-medium"
            onClick={handleToggle}
            aria-label="切换语言"
          >
            {locale === "zh" ? "中文" : "English"}
          </Button>
        </div>
      </div>
    </header>
  );
}
