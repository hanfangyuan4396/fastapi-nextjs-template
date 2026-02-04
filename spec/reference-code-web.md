# 参考实现：前端密码与用户信息功能

以下代码来自当前项目的前端实现，用于复用“Navbar 用户信息 + 修改密码 + 忘记密码”能力。

## 1. Auth 服务封装

文件：`web/src/service/auth.ts`

```ts
import { httpGet, httpPost, type ApiResponse } from "./http";

export type LoginPayload = {
  username: string;
  password: string;
};

export type LoginData = {
  access_token: string;
  refresh_expires_at?: number;
};

export type LoginResponse = ApiResponse<LoginData>;

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  return httpPost<LoginData>("/auth/login", payload, { credentials: "include" });
}

export type UserProfile = {
  id: string;
  username: string;
  role: string;
  is_active: boolean;
  token_version: number;
};

export type MeResponse = ApiResponse<UserProfile>;

export async function getMe(): Promise<MeResponse> {
  return httpGet<UserProfile>("/auth/me", undefined, { credentials: "include" });
}

export type LogoutResponse = ApiResponse<null>;

export async function logout(): Promise<LogoutResponse> {
  return httpPost<null>("/auth/logout", undefined, { credentials: "include" });
}

// ===== Password =====

export type ChangePasswordPayload = {
  old_password: string;
  new_password: string;
  confirm_password: string;
};

export type ChangePasswordResponse = ApiResponse<null>;

export async function changePassword(
  payload: ChangePasswordPayload
): Promise<ChangePasswordResponse> {
  return httpPost<null>("/auth/password/change", payload, { credentials: "include" });
}

export type SendResetCodePayload = {
  email: string;
};

export type SendResetCodeResponse = ApiResponse<null>;

export async function sendResetCode(
  payload: SendResetCodePayload
): Promise<SendResetCodeResponse> {
  return httpPost<null>("/auth/password/reset/send-code", payload, { credentials: "include" });
}

export type ResetPasswordPayload = {
  email: string;
  code: string;
  new_password: string;
  confirm_password: string;
};

export type ResetPasswordResponse = ApiResponse<null>;

export async function resetPassword(
  payload: ResetPasswordPayload
): Promise<ResetPasswordResponse> {
  return httpPost<null>("/auth/password/reset/confirm", payload, { credentials: "include" });
}

// ===== Registration (email + OTP) =====

export type SendRegisterCodePayload = {
  email: string;
};

export type SendRegisterCodeResponse = ApiResponse<null>;

export async function sendRegisterCode(
  payload: SendRegisterCodePayload
): Promise<SendRegisterCodeResponse> {
  return httpPost<null>("/auth/register/send-code", payload, { credentials: "include" });
}

export type VerifyAndCreatePayload = {
  email: string;
  code: string;
  password: string;
};

export type VerifyAndCreateData = {
  access_token: string;
  refresh_expires_at?: number;
};

export type VerifyAndCreateResponse = ApiResponse<VerifyAndCreateData>;

export async function verifyAndCreate(
  payload: VerifyAndCreatePayload
): Promise<VerifyAndCreateResponse> {
  return httpPost<VerifyAndCreateData>("/auth/register/verify-and-create", payload, {
    credentials: "include",
  });
}
```

## 2. 当前用户 Hook

文件：`web/src/lib/use-current-user.ts`

```ts
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
```

## 3. Navbar 用户信息与菜单

文件：`web/src/components/navbar.tsx`

```tsx
import { useCallback, useMemo, useState } from "react";
import { useTranslations } from "next-intl";

import { LanguagesIcon, LogOutIcon, MessageCircleIcon, MenuIcon, UserRoundIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { LocaleSwitcher } from "./locale-switcher";
import { logout } from "@/service/auth";
import { clearAccessToken } from "@/lib/auth";
import { useCurrentUser } from "@/lib/use-current-user";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { ChangePasswordDialog } from "@/components/change-password-dialog";

export function Navbar() {
  const t = useTranslations();
  const router = useRouter();
  const { user } = useCurrentUser();
  const [logoutOpen, setLogoutOpen] = useState(false);
  const [logoutSubmitting, setLogoutSubmitting] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);

  const displayName = user?.username || t("nav.userUnknown");
  const avatarText = useMemo(() => {
    if (!user?.username) return "?";
    return user.username.trim().charAt(0).toUpperCase() || "?";
  }, [user?.username]);

  // ...原 Navbar 逻辑略...

  return (
    <header className="border-b bg-background">
      {/* ...导航链接... */}
      <div className="hidden items-center gap-3 sm:flex">
        <LocaleSwitcher />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="flex items-center gap-3 rounded-full border border-transparent px-2 py-1 text-sm transition-colors hover:border-border hover:bg-accent/50"
              type="button"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                {avatarText}
              </div>
              <span className="max-w-[180px] truncate text-foreground">{displayName}</span>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              {t("nav.account")}
            </DropdownMenuLabel>
            <DropdownMenuItem onSelect={() => setChangePasswordOpen(true)}>
              {t("nav.changePassword")}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={() => setLogoutOpen(true)}>
              <LogOutIcon className="mr-2 h-4 w-4" />
              {t("nav.logout")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <ConfirmDialog ... />
      <ChangePasswordDialog
        open={changePasswordOpen}
        onClose={() => setChangePasswordOpen(false)}
      />
    </header>
  );
}
```

## 4. 修改密码弹窗（含密码可见性图标）

文件：`web/src/components/change-password-dialog.tsx`

```tsx
"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslations } from "next-intl";

import { EyeIcon, EyeOffIcon } from "lucide-react";
import { changePassword } from "@/service/auth";
import { withToast } from "@/lib/withToast";
import { Button } from "@/components/ui/button";

export function ChangePasswordDialog({ open, onClose }: ChangePasswordDialogProps) {
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
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 px-4 py-6" onClick={handleClose}>
      <div className="w-full max-w-md rounded-2xl border bg-background p-6 shadow-xl" onClick={(event) => event.stopPropagation()}>
        <h3 className="text-lg font-semibold text-foreground">{t("auth.password.changeTitle")}</h3>
        <p className="mt-2 text-sm text-muted-foreground">{t("auth.password.changeDescription")}</p>
        {/* 示例：旧密码输入框 */}
        <div className="relative">
          <input
            id="oldPassword"
            type={showOldPassword ? "text" : "password"}
            className="w-full rounded-md border px-3 py-2 pr-12 outline-none"
            {...register("oldPassword", { required: t("auth.password.errors.oldPasswordRequired") })}
          />
          <button
            type="button"
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground hover:text-foreground"
            onClick={() => setShowOldPassword((prev) => !prev)}
          >
            {showOldPassword ? <EyeOffIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}
```

## 5. 忘记密码弹窗（含密码可见性图标）

文件：`web/src/app/login/components/reset-password-dialog.tsx`

```tsx
"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslations } from "next-intl";

import { EyeIcon, EyeOffIcon } from "lucide-react";
import { resetPassword, sendResetCode } from "@/service/auth";
import { withToast } from "@/lib/withToast";
import { Button } from "@/components/ui/button";

export function ResetPasswordDialog({ open, onClose }: ResetPasswordDialogProps) {
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
    defaultValues: { email: "", code: "", newPassword: "", confirmPassword: "" },
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
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 px-4 py-6" onClick={handleClose}>
      <div className="w-full max-w-md rounded-2xl border bg-background p-6 shadow-xl" onClick={(event) => event.stopPropagation()}>
        <h3 className="text-lg font-semibold text-foreground">{t("auth.reset.title")}</h3>
        <p className="mt-2 text-sm text-muted-foreground">{t("auth.reset.description")}</p>
        {/* 示例：新密码输入框 */}
        <div className="relative">
          <input
            id="resetPassword"
            type={showNewPassword ? "text" : "password"}
            className="w-full rounded-md border px-3 py-2 pr-12 outline-none"
            {...register("newPassword", { required: t("auth.reset.errors.newPasswordRequired") })}
          />
          <button
            type="button"
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground hover:text-foreground"
            onClick={() => setShowNewPassword((prev) => !prev)}
          >
            {showNewPassword ? <EyeOffIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}
```

## 6. 登录页入口（含密码可见性图标）

文件：`web/src/app/login/page.tsx`

```tsx
import { ResetPasswordDialog } from "./components/reset-password-dialog";
import { EyeIcon, EyeOffIcon } from "lucide-react";

// ...原有登录逻辑...

<div className="relative">
  <input
    id="password"
    type={showPassword ? "text" : "password"}
    className="w-full rounded-md border px-3 py-2 pr-12 outline-none"
    {...register("password", { required: t("auth.login.errors.passwordRequired") })}
  />
  <button
    type="button"
    className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground hover:text-foreground"
    onClick={() => setShowPassword((prev) => !prev)}
  >
    {showPassword ? <EyeOffIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
  </button>
</div>

<button
  type="button"
  className="mt-3 text-center text-sm text-blue-600 hover:underline"
  onClick={() => setResetOpen(true)}
>
  {t("auth.login.forgotPassword")}
</button>

<ResetPasswordDialog open={resetOpen} onClose={() => setResetOpen(false)} />
```

## 7. 注册页密码可见性图标

文件：`web/src/app/register/page.tsx`

```tsx
import { EyeIcon, EyeOffIcon } from "lucide-react";

// ...原有注册逻辑...

<div className="relative">
  <input
    id="password"
    type={showPassword ? "text" : "password"}
    className="w-full rounded-md border px-3 py-2 pr-12 outline-none"
    {...register("password", { required: t("auth.register.errors.passwordRequired") })}
  />
  <button
    type="button"
    className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground hover:text-foreground"
    onClick={() => setShowPassword((prev) => !prev)}
  >
    {showPassword ? <EyeOffIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
  </button>
</div>

<div className="relative">
  <input
    id="confirmPassword"
    type={showConfirmPassword ? "text" : "password"}
    className="w-full rounded-md border px-3 py-2 pr-12 outline-none"
    {...register("confirmPassword", { required: t("auth.register.errors.confirmPasswordRequired") })}
  />
  <button
    type="button"
    className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-muted-foreground hover:text-foreground"
    onClick={() => setShowConfirmPassword((prev) => !prev)}
  >
    {showConfirmPassword ? <EyeOffIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
  </button>
</div>
```

## 8. 登录页忘记密码与注册左右布局

文件：`web/src/app/login/page.tsx`

```tsx
<div className="mt-4 flex items-center justify-between text-sm text-gray-600">
  <button
    type="button"
    className="text-blue-600 hover:underline"
    onClick={() => setResetOpen(true)}
  >
    {t("auth.login.forgotPassword")}
  </button>
  <Link href="/register" className="text-blue-600 hover:underline">
    {t("auth.login.goRegister")}
  </Link>
</div>
```

## 9. 测试

### 9.1 Auth service 测试

文件：`web/tests/unit/auth-service.test.ts`

```ts
it("calls getMe with credentials", async () => {
  // 目的：获取当前用户接口使用正确路径与参数
  await getMe();

  expect(httpGet).toHaveBeenCalledWith(
    "/auth/me",
    undefined,
    { credentials: "include" }
  );
});
```

### 9.2 修改密码弹窗测试

文件：`web/tests/components/change-password-dialog.test.tsx`

```tsx
it("submits change password when form is valid", async () => {
  // 目的：验证提交表单时调用修改密码接口
  vi.mocked(changePassword).mockResolvedValue({ code: 0, message: "", data: null });
  const user = userEvent.setup();
  const onClose = vi.fn();

  renderWithIntl(<ChangePasswordDialog open onClose={onClose} />);

  await user.type(screen.getByLabelText("旧密码"), "oldpass");
  await user.type(screen.getByLabelText("新密码"), "newpass1");
  await user.type(screen.getByLabelText("确认新密码"), "newpass1");
  await user.click(screen.getByRole("button", { name: "保存修改" }));

  expect(changePassword).toHaveBeenCalledWith({
    old_password: "oldpass",
    new_password: "newpass1",
    confirm_password: "newpass1",
  });
});
```

### 9.3 忘记密码弹窗测试

文件：`web/tests/components/reset-password-dialog.test.tsx`

```tsx
it("submits reset password when form is valid", async () => {
  // 目的：提交表单时调用重置密码接口
  vi.mocked(resetPassword).mockResolvedValue({ code: 0, message: "", data: null });
  const user = userEvent.setup();

  renderWithIntl(<ResetPasswordDialog open onClose={vi.fn()} />);

  await user.type(screen.getByLabelText("邮箱"), "reset@example.com");
  await user.type(screen.getByLabelText("验证码"), "123456");
  await user.type(screen.getByLabelText("新密码"), "newpass1");
  await user.type(screen.getByLabelText("确认新密码"), "newpass1");
  await user.click(screen.getByRole("button", { name: "重置密码" }));

  expect(resetPassword).toHaveBeenCalledWith({
    email: "reset@example.com",
    code: "123456",
    new_password: "newpass1",
    confirm_password: "newpass1",
  });
});
```
