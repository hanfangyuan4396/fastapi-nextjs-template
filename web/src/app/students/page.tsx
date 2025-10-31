"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import { listStudents, type Student } from "@/service/students";

export default function StudentsPage() {
  const t = useTranslations();
  const [items, setItems] = useState<Student[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await listStudents({ page: 1, page_size: 10 });
        if (mounted && res.code === 0 && res.data) {
          setItems(res.data.items);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <h1 className="mb-4 text-xl font-semibold">{t("nav.students")}</h1>

      {loading ? (
        <div className="rounded-md border p-6 text-center text-sm text-muted-foreground">
          {t("common.loading")}
        </div>
      ) : items.length === 0 ? (
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
