"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

import { getAccessToken, setAccessToken } from "@/lib/auth";
import { httpPost } from "@/service/http";

export function RequireAuth(props: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const token = getAccessToken();
      if (token) {
        if (mounted) setIsChecking(false);
        return;
      }

      // 无内存 token 时，尝试通过 HttpOnly 刷新 Cookie 静默获取新的 access token
      try {
        const res = await httpPost<{ access_token?: string | null }>("/auth/refresh");
        if (res.code === 0 && res.data?.access_token) {
          setAccessToken(res.data.access_token);
          if (mounted) setIsChecking(false);
          return;
        }
      } catch {
        // 忽略异常，统一走登录
      }

      if (!mounted) return;
      const search = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${search}`);
    })();

    return () => {
      mounted = false;
    };
  }, [router, pathname]);

  // 在检查完成前不渲染子节点，避免内容闪现
  if (isChecking) {
    return null;
  }

  return <>{props.children}</>;
}
