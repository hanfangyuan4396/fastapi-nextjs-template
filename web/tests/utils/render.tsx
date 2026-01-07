import React, { type ReactElement } from "react";
import { render, type RenderOptions } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";

import { messages } from "./messages";

type WrapperOptions = { locale?: string };

function Providers({
  children,
  locale = "zh",
}: {
  children: React.ReactNode;
  locale?: string;
}) {
  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      {children}
    </NextIntlClientProvider>
  );
}

export function renderWithIntl(
  ui: ReactElement,
  options?: RenderOptions & WrapperOptions
) {
  const { locale, ...rest } = options ?? {};
  return render(ui, {
    wrapper: ({ children }) => <Providers locale={locale}>{children}</Providers>,
    ...rest,
  });
}
