# 项目说明

本前端项目基于 Next.js 15 (App Router) 与 TypeScript，按照 `spec/frontend-student-management.md` 中的需求，用于对接 FastAPI 后端的学生管理系统。

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
