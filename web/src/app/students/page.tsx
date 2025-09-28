import { Suspense } from "react";

import { StudentsClient } from "./students-client";

export default function StudentsPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <h1 className="mb-4 text-xl font-semibold">学生管理</h1>
      <Suspense fallback={<div>加载中...</div>}>
        <StudentsClient />
      </Suspense>
    </div>
  );
}
