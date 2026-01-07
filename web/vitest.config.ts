import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

const alias = {
  "@": fileURLToPath(new URL("./src", import.meta.url)),
};

export default defineConfig({
  test: {
    projects: [
      {
        resolve: { alias },
        test: {
          name: "node",
          environment: "node",
          include: ["tests/unit/**/*.test.{ts,tsx}", "tests/integration/**/*.test.{ts,tsx}"],
          setupFiles: ["./tests/setup/env.setup.ts", "./tests/setup/msw.setup.ts"],
          restoreMocks: true,
          mockReset: true,
          clearMocks: true,
        },
      },
      {
        resolve: { alias },
        test: {
          name: "components",
          environment: "happy-dom",
          include: ["tests/components/**/*.test.{ts,tsx}"],
          setupFiles: [
            "./tests/setup/env.setup.ts",
            "./tests/setup/happydom.setup.ts",
            "./tests/setup/msw.setup.ts"
          ],
          restoreMocks: true,
          mockReset: true,
          clearMocks: true,
        },
      },
    ],
  },
});
