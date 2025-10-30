"use client";

import { useTranslations } from "next-intl";

export function Footer() {
  const t = useTranslations();

  return (
    <footer className="border-t bg-muted/30">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-center text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:text-left">
        <p>{t("footer.copyright", { year: new Date().getFullYear() })}</p>
        <p>{t("footer.poweredBy")}</p>
      </div>
    </footer>
  );
}
