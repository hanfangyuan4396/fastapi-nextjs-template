import { Suspense } from "react";
import { useTranslations } from "next-intl";

import { StudentsManagementClient } from "./students-management-client";

export default function StudentsManagementPage() {
  const t = useTranslations();

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <h1 className="mb-4 text-xl font-semibold">{t("title")}</h1>
      <Suspense fallback={<div>{t("common.loading")}</div>}>
        <StudentsManagementClient />
      </Suspense>
    </div>
  );
}
