import { getTranslations } from "next-intl/server";

import { listStudents, type Student } from "@/service/students";

export default async function StudentPage() {
  const t = await getTranslations();

  const res = await listStudents({ page: 1, page_size: 10 });
  const items: Student[] = (res.code === 0 && res.data ? res.data.items : []) as Student[];

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <h1 className="mb-4 text-xl font-semibold">{t("nav.student")}</h1>

      {items.length === 0 ? (
        <div className="rounded-md border p-6 text-center text-sm text-muted-foreground">
          {t("common.noData")}
        </div>
      ) : (
        <div className="overflow-hidden rounded-md border">
          <ul className="divide-y">
            {items.map((it) => (
              <li key={it.id} className="px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium text-foreground">{it.name}</span>
                  <span className="text-sm text-muted-foreground">{it.student_id}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
