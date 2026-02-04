"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { useTranslations } from "next-intl";
import { EyeIcon, EyeOffIcon } from "lucide-react";

import { login, type LoginPayload } from "@/service/auth";
import { setAccessToken } from "@/lib/auth";
import { ResetPasswordDialog } from "./components/reset-password-dialog";

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
   const [showPassword, setShowPassword] = useState(false);
   const [resetOpen, setResetOpen] = useState(false);

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
       <h1 className="mb-6 text-center text-2xl font-semibold">
         {t("auth.login.title")}
       </h1>

       <form onSubmit={onSubmit} className="space-y-4">
         <div className="space-y-2">
           <label htmlFor="username" className="block text-sm font-medium">
             {t("auth.login.username")}
           </label>
           <input
             id="username"
             type="text"
             className="w-full rounded-md border px-3 py-2 outline-none"
             {...register("username", {
               required: t("auth.login.errors.usernameRequired"),
             })}
           />
           {errors.username?.message ? (
             <p className="text-xs text-red-500">{errors.username.message}</p>
           ) : null}
         </div>

         <div className="space-y-2">
           <label htmlFor="password" className="block text-sm font-medium">
             {t("auth.login.password")}
           </label>
           <div className="relative">
             <input
               id="password"
               type={showPassword ? "text" : "password"}
               className="w-full rounded-md border px-3 py-2 pr-12 outline-none"
               {...register("password", {
                 required: t("auth.login.errors.passwordRequired"),
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

         {errorMsg ? (
           <div className="text-sm text-red-600">{errorMsg}</div>
         ) : null}

         <button
           type="submit"
           disabled={isSubmitting}
           className="w-full rounded-md bg-black px-4 py-2 text-white disabled:opacity-60"
         >
           {isSubmitting ? t("auth.login.submitting") : t("auth.login.submit")}
         </button>
       </form>

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

       <ResetPasswordDialog open={resetOpen} onClose={() => setResetOpen(false)} />
     </div>
   );
 }
