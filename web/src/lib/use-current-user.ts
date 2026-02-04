"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getMe, type UserProfile } from "@/service/auth";
import { getAccessToken, getAuthChangedEventName } from "@/lib/auth";

type CurrentUserState = {
  user: UserProfile | null;
  loading: boolean;
  refresh: () => Promise<void>;
};

export function useCurrentUser(): CurrentUserState {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const activeRef = useRef(true);

  const refresh = useCallback(async () => {
    if (!getAccessToken()) {
      if (activeRef.current) {
        setUser(null);
        setLoading(false);
      }
      return;
    }

    if (activeRef.current) {
      setLoading(true);
    }

    try {
      const res = await getMe();
      if (!activeRef.current) return;
      if (res.code === 0 && res.data) {
        setUser(res.data);
      } else {
        setUser(null);
      }
    } catch {
      if (activeRef.current) {
        setUser(null);
      }
    } finally {
      if (activeRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    activeRef.current = true;
    void refresh();
    return () => {
      activeRef.current = false;
    };
  }, [refresh]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const handler = () => {
      void refresh();
    };
    const eventName = getAuthChangedEventName();
    window.addEventListener(eventName, handler);
    return () => {
      window.removeEventListener(eventName, handler);
    };
  }, [refresh]);

  return { user, loading, refresh };
}
