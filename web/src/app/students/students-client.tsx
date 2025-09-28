"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { listStudents, type Student } from "@/service/students";
import { CreateStudentDialog } from "./students-create-dialog";

const DEFAULT_PAGE_SIZE = 10;

export function StudentsClient() {
  const [items, setItems] = useState<Student[]>([]);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(DEFAULT_PAGE_SIZE);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);

  const totalPages = useMemo(() => {
    if (pageSize <= 0) return 1;
    return Math.max(1, Math.ceil(total / pageSize));
  }, [total, pageSize]);

  const fetchData = useCallback(async (targetPage: number) => {
    setLoading(true);
    try {
      const res = await listStudents({ page: targetPage, page_size: pageSize });
      if (res.code === 0 && res.data) {
        setItems(res.data.items);
        setTotal(res.data.total);
      }
    } finally {
      setLoading(false);
    }
  }, [pageSize]);

  useEffect(() => {
    fetchData(page);
  }, [fetchData, page]);

  const handlePrev = useCallback(() => {
    setPage((p) => Math.max(1, p - 1));
  }, []);
  const handleNext = useCallback(() => {
    setPage((p) => Math.min(totalPages, p + 1));
  }, [totalPages]);
  // 已移除未使用的 handleGoto 以消除 lint 警告

  const refresh = useCallback(async () => {
    await fetchData(1);
    setPage(1);
  }, [fetchData]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm text-muted-foreground">
          共 {total} 条
        </div>
        <CreateStudentDialog onCreated={refresh} />
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">ID</TableHead>
              <TableHead>姓名</TableHead>
              <TableHead>学号</TableHead>
              <TableHead>性别</TableHead>
              <TableHead className="text-right">年龄</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((it) => (
              <TableRow key={it.id}>
                <TableCell>{it.id}</TableCell>
                <TableCell>{it.name}</TableCell>
                <TableCell>{it.student_id}</TableCell>
                <TableCell>{it.gender}</TableCell>
                <TableCell className="text-right">{it.age ?? "-"}</TableCell>
              </TableRow>
            ))}
            {items.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={5} className="py-6 text-center text-muted-foreground">
                  暂无数据
                </TableCell>
              </TableRow>
            )}
            {loading && (
              <TableRow>
                <TableCell colSpan={5} className="py-6 text-center text-muted-foreground">
                  加载中...
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between gap-3">
        <div className="text-sm text-muted-foreground">
          第 {page} / {totalPages} 页
        </div>
        <Pagination>
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious href="#" onClick={(e) => { e.preventDefault(); handlePrev(); }} />
            </PaginationItem>
            <PaginationItem>
              <PaginationLink href="#" isActive>{page}</PaginationLink>
            </PaginationItem>
            <PaginationItem>
              <PaginationNext href="#" onClick={(e) => { e.preventDefault(); handleNext(); }} />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      </div>

      <div className="flex items-center justify-end">
        <Button variant="ghost" onClick={() => fetchData(page)} disabled={loading}>
          刷新
        </Button>
      </div>
    </div>
  );
}
