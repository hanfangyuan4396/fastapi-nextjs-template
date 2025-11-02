import { getRequestConfig } from "next-intl/server";
import { headers } from "next/headers";
import { locales, defaultLocale, type Locale } from "./locales";

// next-intl 配置
export default getRequestConfig(async () => {
  // 从中间件设置的请求头中获取语言
  const headersList = await headers();
  let locale = headersList.get("x-locale") as Locale | null;

  // 验证语言是否支持
  if (!locale || !locales.includes(locale as Locale)) {
    locale = defaultLocale;
  }

  // 加载对应语言的翻译文件
  const messages = {
    ...(await import(`./messages/${locale}/common.json`)).default,
    ...(await import(`./messages/${locale}/home.json`)).default,
    ...(await import(`./messages/${locale}/students.json`)).default,
    ...(await import(`./messages/${locale}/auth.json`)).default,
  };

  return {
    locale,
    messages,
  };
});
