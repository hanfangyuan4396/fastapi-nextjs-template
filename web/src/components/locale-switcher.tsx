"use client";

import { useLocale } from "next-intl";
import { useTransition } from "react";
import { locales, type Locale } from "@/i18n/locales";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// 语言显示名称
const localeNames: Record<Locale, string> = {
  zh: "中文",
  en: "English",
};

export function LocaleSwitcher() {
  const locale = useLocale() as Locale;
  const [isPending, startTransition] = useTransition();

  const handleLocaleChange = (newLocale: string) => {
    startTransition(() => {
      // 设置 Cookie
      document.cookie = `locale=${newLocale}; path=/; max-age=${365 * 24 * 60 * 60}; SameSite=Lax`;

      // 刷新页面以应用新语言
      window.location.reload();
    });
  };

  return (
    <Select
      value={locale}
      onValueChange={handleLocaleChange}
      disabled={isPending}
    >
      <SelectTrigger className="w-[120px]">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {locales.map((loc) => (
          <SelectItem key={loc} value={loc}>
            {localeNames[loc]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
