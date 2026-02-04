"use client";

import { useEffect, useState } from "react";

import { getMe, type UserProfile } from "@/service/auth";

type CurrentUserState = {
  user: UserProfile | null;
  loading: boolean;
};

export function useCurrentUser(): CurrentUserState {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    const fetchUser = async () => {
      try {
        const res = await getMe();
        if (!active) return;
        if (res.code === 0 && res.data) {
          setUser(res.data);
        } else {
          setUser(null);
        }
      } catch {
        if (active) setUser(null);
      } finally {
        if (active) setLoading(false);
      }
    };

    void fetchUser();

    return () => {
      active = false;
    };
  }, []);

  return { user, loading };
}
