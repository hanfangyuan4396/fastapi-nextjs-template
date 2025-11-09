"use client";

import { toast } from "sonner";

export type WithToastOptions = {
  success?: string;
  error?: string;
};

export async function withToast<T>(
  p: Promise<T>,
  opts: WithToastOptions = {}
): Promise<T> {
  try {
    const result = await p;
    if (opts.success) {
      toast.success(opts.success);
    }
    return result;
  } catch (e: unknown) {
    const message =
      (e instanceof Error && e.message) ||
      opts.error ||
      "Request failed";
    toast.error(message);
    throw e;
  }
}
