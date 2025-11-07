"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

import { getCurrentUserRole } from "@/lib/auth";

export function RequireRole(props: { children: React.ReactNode; required: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const [checked, setChecked] = useState(false);

  const hasAccess = useMemo(() => {
    const role = getCurrentUserRole();
    if (!role) return null; // 角色未知（通常在刚刷新完成之前的短瞬间）
    return role === props.required;
  }, [pathname, props.required]);

  useEffect(() => {
    if (hasAccess === null) return; // 等待角色解码
    if (hasAccess === true) {
      setChecked(true);
      return;
    }
    // 无权限：统一跳转首页
    router.replace("/");
  }, [hasAccess, router]);

  if (!checked) return null;
  return <>{props.children}</>;
}
