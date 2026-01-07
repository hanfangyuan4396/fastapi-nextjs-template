# 项目说明
本前端项目基于 Next.js 16 (App Router) 与 TypeScript，按照 `spec/frontend-student-management.md` 中的需求，用于对接 FastAPI 后端的学生管理系统。

## 初始化记录

```bash
npx create-next-app@latest web1 \
  --ts \
  --app \
  --eslint \
  --src-dir \
  --use-npm \
  --import-alias "@/*" \
  --tailwind \
  --use-turbopack
```

- 使用 `npm` 作为包管理器。
- `--use-turbopack` 启用 Turbopack 开发构建工具。

## UI 组件库集成

```bash
npx shadcn@latest init
```
- 选择基础主题色：`Neutral`。
- CLI 自动更新 `src/app/globals.css`、`src/lib/utils.ts` 并生成 `components.json`。

### 已添加组件

```bash
npx shadcn@latest add button input label select form table dropdown-menu pagination
```
- 组件文件生成于 `src/components/ui/`。

## 测试

- 测试框架：Vitest + Testing Library，配合 MSW 与 happy-dom。
- 测试目录：`tests/`（按 `unit/`、`integration/`、`components/` 分类）。
- 运行测试：
  - `npm run test`
  - `npm run test:coverage`

## 运行与构建

- 安装依赖：`npm install`
- 本地开发：`npm run dev`
- 生产构建：`npm run build`
- 生产启动（standalone 输出）：复制public目录 和.next/static目录到.next/standalone，然后执行`node .next/standalone/server.js`
- `npm run start` 使用 `next start`，与 `output: "standalone"` 的部署方式不匹配，仅在非 standalone 场景使用
