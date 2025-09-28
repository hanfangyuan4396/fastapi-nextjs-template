"use client";

import { useTranslations } from "next-intl";

export default function HomePage() {
  const t = useTranslations("home");

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-4 py-16 sm:px-6 sm:py-20">
      <h1 className="text-3xl font-semibold sm:text-4xl">{t("title")}</h1>
      <p className="text-lg text-muted-foreground">{t("subtitle")}</p>
      <p className="text-base leading-7 text-muted-foreground">{t("description")}</p>
    </div>
  );
}
