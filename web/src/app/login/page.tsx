"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { useTranslations } from "next-intl";

import { login, type LoginPayload } from "@/service/auth";
import { setAccessToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const t = useTranslations();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginPayload>({ defaultValues: { username: "", password: "" } });

  const [errorMsg, setErrorMsg] = useState<string>("");


  const onSubmit = handleSubmit(async (values) => {
    setErrorMsg("");
    const res = await login(values);
    if (res.code === 0 && res.data?.access_token) {
      setAccessToken(res.data.access_token);
      const raw = searchParams.get("next");
      const nextPath =
        raw && raw.startsWith("/") && !raw.startsWith("//") && !raw.includes("://")
          ? raw
          : "/";
      router.replace(nextPath);
    } else {
      setErrorMsg(res.message || t("auth.login.error"));
    }
  });

  return (
    <div className="mx-auto flex min-h-[60vh] max-w-sm flex-col justify-center px-4 py-10">
      <h1 className="mb-6 text-center text-2xl font-semibold">{t("auth.login.title")}</h1>

      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="username" className="block text-sm font-medium">
            {t("auth.login.username")}
          </label>
          <input
            id="username"
            type="text"
            className="w-full rounded-md border px-3 py-2 outline-none"
            {...register("username", { required: t("auth.login.errors.usernameRequired") })}
          />
          {errors.username?.message ? (
            <p className="text-xs text-red-500">{errors.username.message}</p>
          ) : null}
        </div>

        <div className="space-y-2">
          <label htmlFor="password" className="block text-sm font-medium">
            {t("auth.login.password")}
          </label>
          <input
            id="password"
            type="password"
            className="w-full rounded-md border px-3 py-2 outline-none"
            {...register("password", { required: t("auth.login.errors.passwordRequired") })}
          />
          {errors.password?.message ? (
            <p className="text-xs text-red-500">{errors.password.message}</p>
          ) : null}
        </div>

        {errorMsg ? <div className="text-sm text-red-600">{errorMsg}</div> : null}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-md bg-black px-4 py-2 text-white disabled:opacity-60"
        >
          {isSubmitting ? t("auth.login.submitting") : t("auth.login.submit")}
        </button>
      </form>
    </div>
  );
}
