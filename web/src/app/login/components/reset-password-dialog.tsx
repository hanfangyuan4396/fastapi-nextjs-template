"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslations } from "next-intl";
import { EyeIcon, EyeOffIcon } from "lucide-react";

import { resetPassword, sendResetCode } from "@/service/auth";
import { withToast } from "@/lib/withToast";
import { Button } from "@/components/ui/button";

type ResetPasswordDialogProps = {
  open: boolean;
  onClose: () => void;
};

type ResetPasswordFormValues = {
  email: string;
  code: string;
  newPassword: string;
  confirmPassword: string;
};

export function ResetPasswordDialog({
  open,
  onClose,
}: ResetPasswordDialogProps) {
  const t = useTranslations();
  const [errorMsg, setErrorMsg] = useState("");
  const [isSendingCode, setIsSendingCode] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormValues>({
    defaultValues: {
      email: "",
      code: "",
      newPassword: "",
      confirmPassword: "",
    },
  });

  const watchedEmail = watch("email");

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setTimeout(() => setCooldown((prev) => prev - 1), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  const handleClose = () => {
    reset();
    setErrorMsg("");
    setIsSendingCode(false);
    setCooldown(0);
    onClose();
  };

  const handleSendCode = async () => {
    setErrorMsg("");
    if (!watchedEmail) {
      setErrorMsg(t("auth.reset.errors.emailRequired"));
      return;
    }
    if (cooldown > 0 || isSendingCode) return;

    setIsSendingCode(true);
    try {
      await withToast(
        (async () => {
          const res = await sendResetCode({ email: watchedEmail });
          if (res.code !== 0) {
            throw new Error(res.message || t("auth.reset.errorGeneric"));
          }
          return res;
        })(),
        {
          success: t("auth.reset.toast.sendCodeSuccess"),
          error: t("auth.reset.toast.sendCodeFail"),
        }
      );
      setCooldown(30);
    } finally {
      setIsSendingCode(false);
    }
  };

  const onSubmit = handleSubmit(async (values) => {
    setErrorMsg("");
    if (values.newPassword !== values.confirmPassword) {
      setErrorMsg(t("auth.reset.errors.passwordNotMatch"));
      return;
    }

    await withToast(
      (async () => {
        const res = await resetPassword({
          email: values.email,
          code: values.code,
          new_password: values.newPassword,
          confirm_password: values.confirmPassword,
        });
        if (res.code !== 0) {
          throw new Error(res.message || t("auth.reset.errorGeneric"));
        }
        return res;
      })(),
      {
        success: t("auth.reset.toast.resetSuccess"),
        error: t("auth.reset.toast.resetFail"),
      }
    );

    handleClose();
  });

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 px-4 py-6"
      onClick={handleClose}
    >
      <div
        className="w-full max-w-md rounded-2xl border bg-background p-6 shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <h3 className="text-lg font-semibold text-foreground">
          {t("auth.reset.title")}
        </h3>
        <p className="mt-2 text-sm text-muted-foreground">
          {t("auth.reset.description")}
        </p>

        <form onSubmit={onSubmit} className="mt-5 space-y-4">
          <div className="space-y-2">
            <label htmlFor="resetEmail" className="block text-sm font-medium">
              {t("auth.reset.email")}
            </label>
            <input
              id="resetEmail"
              type="email"
              className="w-full rounded-md border px-3 py-2 outline-none"
              {...register("email", {
                required: t("auth.reset.errors.emailRequired"),
              })}
            />
            {errors.email?.message ? (
              <p className="text-xs text-red-500">{errors.email.message}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <label htmlFor="resetCode" className="block text-sm font-medium">
              {t("auth.reset.code")}
            </label>
            <div className="flex gap-2">
              <input
                id="resetCode"
                type="text"
                className="w-full rounded-md border px-3 py-2 outline-none"
                {...register("code", {
                  required: t("auth.reset.errors.codeRequired"),
                })}
              />
              <Button
                type="button"
                variant="outline"
                className="shrink-0"
                onClick={handleSendCode}
                disabled={cooldown > 0 || isSendingCode}
              >
                {cooldown > 0
                  ? `${t("auth.reset.sendCode")} (${cooldown}s)`
                  : isSendingCode
                  ? t("auth.reset.sendingCode")
                  : t("auth.reset.sendCode")}
              </Button>
            </div>
            {errors.code?.message ? (
              <p className="text-xs text-red-500">{errors.code.message}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <label htmlFor="resetPassword" className="block text-sm font-medium">
              {t("auth.reset.newPassword")}
            </label>
            <div className="relative">
              <input
                id="resetPassword"
                type={showNewPassword ? "text" : "password"}
                className="w-full rounded-md border px-3 py-2 pr-12 outline-none"
                {...register("newPassword", {
                  required: t("auth.reset.errors.newPasswordRequired"),
                })}
              />
              <button
                type="button"
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground hover:text-foreground"
                onClick={() => setShowNewPassword((prev) => !prev)}
              >
                {showNewPassword ? (
                  <EyeOffIcon className="h-4 w-4" />
                ) : (
                  <EyeIcon className="h-4 w-4" />
                )}
              </button>
            </div>
            {errors.newPassword?.message ? (
              <p className="text-xs text-red-500">{errors.newPassword.message}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <label
              htmlFor="resetConfirmPassword"
              className="block text-sm font-medium"
            >
              {t("auth.reset.confirmPassword")}
            </label>
            <div className="relative">
              <input
                id="resetConfirmPassword"
                type={showConfirmPassword ? "text" : "password"}
                className="w-full rounded-md border px-3 py-2 pr-12 outline-none"
                {...register("confirmPassword", {
                  required: t("auth.reset.errors.confirmPasswordRequired"),
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

          <div className="flex items-center justify-end gap-3 pt-2">
            <Button type="button" variant="outline" onClick={handleClose}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? t("auth.reset.submitting") : t("auth.reset.submit")}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
