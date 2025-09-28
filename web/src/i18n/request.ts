import {getRequestConfig} from 'next-intl/server';
import {headers} from 'next/headers';

export default getRequestConfig(async () => {
  // 从请求头获取语言偏好，默认为英文
  const requestHeaders = await headers();
  const acceptLanguage = requestHeaders.get('accept-language')?.toLowerCase() ?? '';
  const locale = acceptLanguage.startsWith('zh') ? 'zh' : 'en';

  return {
    locale,
    messages: {
      home: (await import(`../messages/${locale}/home.json`)).default
    }
  };
});
