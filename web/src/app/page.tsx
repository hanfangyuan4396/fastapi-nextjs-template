"use client";

import { useTranslations } from "next-intl";

export default function HomePage() {
  const t = useTranslations();

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-4 py-16 sm:px-6 sm:py-20">
      <h1 className="text-3xl font-semibold sm:text-4xl">{t("title")}</h1>
      <p className="text-lg text-muted-foreground">{t("subtitle")}</p>
      <p className="text-base leading-7 text-muted-foreground">{t("description")}</p>
      <section className="mt-2">
        <h2 className="text-xl font-medium">{t("stack.title")}</h2>
        <ul className="mt-3 grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
          <li>
            <span className="font-medium text-foreground">{t("stack.backend.label")}: </span>
            {t("stack.backend.value")}
          </li>
          <li>
            <span className="font-medium text-foreground">{t("stack.frontend.label")}: </span>
            {t("stack.frontend.value")}
          </li>
          <li>
            <span className="font-medium text-foreground">{t("stack.database.label")}: </span>
            {t("stack.database.value")}
          </li>
          <li>
            <span className="font-medium text-foreground">{t("stack.devops.label")}: </span>
            {t("stack.devops.value")}
          </li>
        </ul>
      </section>
    </div>
  );
}
