"use client";

import { useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";

import { getCurrentUserRole, Role } from "@/lib/auth";

export function RequireRole(props: { children: React.ReactNode; required: Role }) {
  const router = useRouter();

  const hasAccess = useMemo(() => {
    const role = getCurrentUserRole();
    if (!role) return null; // 角色未知（通常在刚刷新完成之前的短瞬间）
    return role === props.required;
  }, [props.required]);

  useEffect(() => {
    if (hasAccess === false) {
      // 无权限：统一跳转首页
      router.replace("/");
    }
  }, [hasAccess, router]);

  if (hasAccess !== true) return null; // 等待角色解析或无权限时不渲染
  return <>{props.children}</>;
}
