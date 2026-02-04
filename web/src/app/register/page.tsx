"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { useTranslations } from "next-intl";
import { EyeIcon, EyeOffIcon } from "lucide-react";

import {
  sendRegisterCode,
  verifyAndCreate,
  type VerifyAndCreatePayload,
} from "@/service/auth";
import { setAccessToken } from "@/lib/auth";
import { withToast } from "@/lib/withToast";

type RegisterFormValues = {
  email: string;
  code: string;
  password: string;
  confirmPassword: string;
};

export default function RegisterPage() {
  const t = useTranslations();
  const router = useRouter();
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    defaultValues: {
      email: "",
      code: "",
      password: "",
      confirmPassword: "",
    },
  });

  const watchedEmail = watch("email");

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setTimeout(() => setCooldown((prev) => prev - 1), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  const handleSendCode = async () => {
    setErrorMsg("");
    if (!watchedEmail) {
      setErrorMsg(t("auth.register.errors.emailRequired"));
      return;
    }
    if (cooldown > 0 || isSendingCode) {
      return;
    }

    setIsSendingCode(true);
    try {
      await withToast(
        (async () => {
          const res = await sendRegisterCode({ email: watchedEmail });
          if (res.code !== 0) {
            throw new Error(res.message || "Request failed");
          }
          return res;
        })(),
        {
          success: t("auth.register.toast.sendCodeSuccess"),
          error: t("auth.register.toast.sendCodeFail"),
        }
      );
      setCooldown(30);
    } catch (e: unknown) {
      const msg =
        (e instanceof Error && e.message) || t("auth.register.errorNetwork");
      setErrorMsg(msg);
    } finally {
      setIsSendingCode(false);
    }
  };

  const onSubmit = handleSubmit(async (values) => {
    setErrorMsg("");

    if (values.password !== values.confirmPassword) {
      setErrorMsg(t("auth.register.errors.passwordNotMatch"));
      return;
    }

    const payload: VerifyAndCreatePayload = {
      email: values.email,
      code: values.code,
      password: values.password,
    };

    try {
      const res = await withToast(
        (async () => {
          const res = await verifyAndCreate(payload);
          if (res.code !== 0 || !res.data?.access_token) {
            throw new Error(res.message || t("auth.register.errorGeneric"));
          }
          return res;
        })(),
        {
          success: t("auth.register.toast.registerSuccess"),
          error: t("auth.register.toast.registerFail"),
        }
      );
      // 经过上面的校验，这里可以安全访问 access_token
      if (res.data?.access_token) {
        setAccessToken(res.data.access_token);
      }
      router.replace("/students");
    } catch (e: unknown) {
      const msg =
        (e instanceof Error && e.message) || t("auth.register.errorNetwork");
      setErrorMsg(msg);
    }
  });

  return (
    <div className="mx-auto flex min-h-[60vh] max-w-sm flex-col justify-center px-4 py-10">
      <h1 className="mb-6 text-center text-2xl font-semibold">
        {t("auth.register.title")}
      </h1>

      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="email" className="block text-sm font-medium">
            {t("auth.register.email")}
          </label>
          <input
            id="email"
            type="email"
            className="w-full rounded-md border px-3 py-2 outline-none"
            {...register("email", {
              required: t("auth.register.errors.emailRequired"),
            })}
          />
          {errors.email?.message ? (
            <p className="text-xs text-red-500">{errors.email.message}</p>
          ) : null}
        </div>

        <div className="space-y-2">
          <label htmlFor="code" className="block text-sm font-medium">
            {t("auth.register.code")}
          </label>
          <div className="flex gap-2">
            <input
              id="code"
              type="text"
              className="flex-1 rounded-md border px-3 py-2 outline-none"
              {...register("code", {
                required: t("auth.register.errors.codeRequired"),
              })}
            />
            <button
              type="button"
              onClick={handleSendCode}
              disabled={isSendingCode || cooldown > 0}
              className="whitespace-nowrap rounded-md border border-black px-3 py-2 text-sm font-medium disabled:opacity-60"
            >
              {cooldown > 0
                ? `${t("auth.register.sendCode")} (${cooldown}s)`
                : isSendingCode
                  ? t("auth.register.sendingCode")
                  : t("auth.register.sendCode")}
            </button>
          </div>
          {errors.code?.message ? (
            <p className="text-xs text-red-500">{errors.code.message}</p>
          ) : null}
        </div>

        <div className="space-y-2">
          <label htmlFor="password" className="block text-sm font-medium">
            {t("auth.register.password")}
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              className="w-full rounded-md border px-3 py-2 pr-12 outline-none"
              {...register("password", {
                required: t("auth.register.errors.passwordRequired"),
              })}
            />
            <button
              type="button"
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground hover:text-foreground"
              onClick={() => setShowPassword((prev) => !prev)}
            >
              {showPassword ? (
                <EyeOffIcon className="h-4 w-4" />
              ) : (
                <EyeIcon className="h-4 w-4" />
              )}
            </button>
          </div>
          {errors.password?.message ? (
            <p className="text-xs text-red-500">{errors.password.message}</p>
          ) : null}
        </div>

        <div className="space-y-2">
          <label htmlFor="confirmPassword" className="block text-sm font-medium">
            {t("auth.register.confirmPassword")}
          </label>
          <div className="relative">
            <input
              id="confirmPassword"
              type={showConfirmPassword ? "text" : "password"}
              className="w-full rounded-md border px-3 py-2 pr-12 outline-none"
              {...register("confirmPassword", {
                required: t("auth.register.errors.confirmPasswordRequired"),
              })}
            />
            <button
              type="button"
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground hover:text-foreground"
              onClick={() => setShowConfirmPassword((prev) => !prev)}
            >
              {showConfirmPassword ? (
                <EyeOffIcon className="h-4 w-4" />
              ) : (
                <EyeIcon className="h-4 w-4" />
              )}
            </button>
          </div>
          {errors.confirmPassword?.message ? (
            <p className="text-xs text-red-500">
              {errors.confirmPassword.message}
            </p>
          ) : null}
        </div>

        {errorMsg ? (
          <div className="text-sm text-red-600">{errorMsg}</div>
        ) : null}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-md bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {isSubmitting
            ? t("auth.register.submitting")
            : t("auth.register.submit")}
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-gray-600">
        {t("auth.register.haveAccount")}{" "}
        <Link href="/login" className="text-blue-600 hover:underline">
          {t("auth.register.goLogin")}
        </Link>
      </p>
    </div>
  );
}
