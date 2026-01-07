import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";
import React from "react";

vi.mock("next/image", () => ({
  default: (
    props: React.ComponentProps<"img"> & {
      src: string | { src: string };
      priority?: boolean;
      unoptimized?: boolean;
    }
  ) => {
    const { priority, unoptimized, ...rest } = props;
    void priority;
    void unoptimized;
    const resolvedSrc = typeof rest.src === "string" ? rest.src : rest.src?.src;
    return React.createElement("img", { ...rest, src: resolvedSrc });
  },
}));

afterEach(() => {
  cleanup();
});
