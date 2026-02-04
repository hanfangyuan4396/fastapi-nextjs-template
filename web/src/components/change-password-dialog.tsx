"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslations } from "next-intl";
import { EyeIcon, EyeOffIcon } from "lucide-react";

import { changePassword } from "@/service/auth";
import { withToast } from "@/lib/withToast";
import { Button } from "@/components/ui/button";

type ChangePasswordDialogProps = {
  open: boolean;
  onClose: () => void;
};

type ChangePasswordFormValues = {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
};

export function ChangePasswordDialog({
  open,
  onClose,
}: ChangePasswordDialogProps) {
  const t = useTranslations();
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordFormValues>({
    defaultValues: { oldPassword: "", newPassword: "", confirmPassword: "" },
  });

  const handleClose = () => {
    reset();
    setErrorMsg("");
    onClose();
  };

  const onSubmit = handleSubmit(async (values) => {
    setErrorMsg("");
    if (values.newPassword !== values.confirmPassword) {
      setErrorMsg(t("auth.password.errors.passwordNotMatch"));
      return;
    }

    await withToast(
      (async () => {
        const res = await changePassword({
          old_password: values.oldPassword,
          new_password: values.newPassword,
          confirm_password: values.confirmPassword,
        });
        if (res.code !== 0) {
          throw new Error(res.message || t("auth.password.errorGeneric"));
        }
        return res;
      })(),
      {
        success: t("auth.password.toast.changeSuccess"),
        error: t("auth.password.toast.changeFail"),
      }
    );

    handleClose();
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 px-4 py-6">
      <div
        className="w-full max-w-md rounded-2xl border bg-background p-6 shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <h3 className="text-lg font-semibold text-foreground">
          {t("auth.password.changeTitle")}
        </h3>
        <p className="mt-2 text-sm text-muted-foreground">
          {t("auth.password.changeDescription")}
        </p>

        <form onSubmit={onSubmit} className="mt-5 space-y-4">
          <div className="space-y-2">
            <label htmlFor="oldPassword" className="block text-sm font-medium">
              {t("auth.password.oldPassword")}
            </label>
            <div className="relative">
              <input
                id="oldPassword"
                type={showOldPassword ? "text" : "password"}
                className="w-full rounded-md border px-3 py-2 pr-12 outline-none"
                {...register("oldPassword", {
                  required: t("auth.password.errors.oldPasswordRequired"),
                })}
              />
              <button
                type="button"
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground hover:text-foreground"
                onClick={() => setShowOldPassword((prev) => !prev)}
              >
                {showOldPassword ? (
                  <EyeOffIcon className="h-4 w-4" />
                ) : (
                  <EyeIcon className="h-4 w-4" />
                )}
              </button>
            </div>
            {errors.oldPassword?.message ? (
              <p className="text-xs text-red-500">{errors.oldPassword.message}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <label htmlFor="newPassword" className="block text-sm font-medium">
              {t("auth.password.newPassword")}
            </label>
            <div className="relative">
              <input
                id="newPassword"
                type={showNewPassword ? "text" : "password"}
                className="w-full rounded-md border px-3 py-2 pr-12 outline-none"
                {...register("newPassword", {
                  required: t("auth.password.errors.newPasswordRequired"),
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
            <label htmlFor="confirmPassword" className="block text-sm font-medium">
              {t("auth.password.confirmPassword")}
            </label>
            <div className="relative">
              <input
                id="confirmPassword"
                type={showConfirmPassword ? "text" : "password"}
                className="w-full rounded-md border px-3 py-2 pr-12 outline-none"
                {...register("confirmPassword", {
                  required: t("auth.password.errors.confirmPasswordRequired"),
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
              {isSubmitting
                ? t("auth.password.submitting")
                : t("auth.password.submit")}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
