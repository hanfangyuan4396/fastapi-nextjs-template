"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";

import { getAccessToken } from "@/lib/auth";

export function RequireAuth(props: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      const search = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${search}`);
    }
  }, [router, pathname]);

  return <>{props.children}</>;
}
