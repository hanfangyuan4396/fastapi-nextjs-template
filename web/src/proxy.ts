import { NextRequest, NextResponse } from "next/server";
import { defaultLocale, locales, type Locale } from "./i18n/locales";

// Cookie 名称
const LOCALE_COOKIE_NAME = "locale";

// Cookie 过期时间：365天
const COOKIE_MAX_AGE = 365 * 24 * 60 * 60;

/**
 * 从浏览器 Accept-Language 头中获取首选语言
 */
function getPreferredLocale(acceptLanguage: string | null): Locale {
  if (!acceptLanguage) {
    return defaultLocale;
  }

  // 解析 Accept-Language 头，例如：zh-CN,zh;q=0.9,en;q=0.8
  const languages = acceptLanguage
    .split(",")
    .map((lang) => lang.split(";")[0].trim().toLowerCase());

  // 查找第一个支持的语言
  for (const lang of languages) {
    // 完全匹配，例如 "zh" 或 "en"
    if (locales.includes(lang as Locale)) {
      return lang as Locale;
    }
    // 前缀匹配，例如 "zh-CN" 匹配 "zh"
    const prefix = lang.split("-")[0];
    if (locales.includes(prefix as Locale)) {
      return prefix as Locale;
    }
  }

  return defaultLocale;
}

export function proxy(request: NextRequest) {
  // 1. 优先从 Cookie 中读取用户手动选择的语言
  let locale = request.cookies.get(LOCALE_COOKIE_NAME)?.value as Locale | undefined;

  // 验证 Cookie 中的语言是否有效
  if (locale && !locales.includes(locale)) {
    locale = undefined;
  }

  // 2. 如果 Cookie 中没有，则从浏览器 Accept-Language 头中获取
  if (!locale) {
    const acceptLanguage = request.headers.get("accept-language");
    locale = getPreferredLocale(acceptLanguage);
  }

  // 3. 如果都没有，使用默认语言
  if (!locale) {
    locale = defaultLocale;
  }

  // 创建响应
  const response = NextResponse.next();

  // 设置 Cookie（如果还没有设置）
  if (!request.cookies.get(LOCALE_COOKIE_NAME)) {
    response.cookies.set(LOCALE_COOKIE_NAME, locale, {
      maxAge: COOKIE_MAX_AGE,
      path: "/",
      sameSite: "lax",
    });
  }

  // 设置自定义请求头，供 next-intl 使用
  response.headers.set("x-locale", locale);

  return response;
}

export const config = {
  // 匹配所有路径，除了静态资源和 API 路由
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
