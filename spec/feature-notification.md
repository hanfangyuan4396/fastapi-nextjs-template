# 前端全局消息通知（Toast/Notification）功能规格

## 需求描述
- 在前端统一提供“消息通知”能力，用于在用户触发的后端接口调用成功或失败时，给出即时反馈提示（如创建学生成功/失败、更新、删除等）。
- 通知需要全局可用、可国际化、可配置（样式、时长、位置），并在 App Router 与客户端组件中使用便捷。

## 需求目标
- 成功与失败均给出明确、可读、可国际化的提示文案。
- 全局只需一次性注入 Provider，不侵入现有页面结构。
- 为网络/后端错误、业务错误建立清晰的展示策略：显示后端返回的 `message` 字段（后端返回统一格式 `code/message/data`）。
- 提供统一的 API 请求封装与 `withToast` 工具，降低重复代码、保持一致 UX。
- 兼容 SSR/RSC 架构：通知只在客户端环境渲染，不影响服务器端渲染。

## 技术方案（Next.js 最佳实践）
### 1) 通知库选择
- 采用 `sonner`：轻量、现代、API 简洁，适配 Next.js App Router，支持丰富样式与可关闭按钮。

### 2) Provider 注入与全局可用
- 新增 `web/src/providers/NotificationProvider.tsx`（客户端组件）承载全局通知容器。
- 在 `web/src/app/layout.tsx` 中，于 `NextIntlClientProvider` 内部引入该 Provider，确保全局页面均可显示通知。
- 配置建议：开启 `richColors`、`closeButton`；设置 `position`（如 `top-right`）与 `duration`（如 3000-4000ms）。

### 3) 统一 API 客户端封装
- 新增 `web/src/lib/api-client.ts`，封装统一的 `apiFetch`：
  - 负责拼接后端 `BASE_URL`（如 `/api`）、附带鉴权头（若需要）、与 JSON 解析。
  - 非 2xx 统一抛出应用层错误，错误消息从响应体的 `message` 字段提取（后端已统一 `code/message/data`）。
  - 是否弹出通知由调用层控制（避免底层直接耦合 UI，保留灵活性）。

### 4) `withToast` 工具（统一成功/失败提示）
- 新增 `web/src/lib/withToast.ts`：接收一个 Promise（通常是 `apiFetch` 调用），并在成功/失败时用 `sonner` 弹出提示。
- 支持自定义成功/失败文案与基于 i18n 的多语言消息；不新增 loading 状态。

### 5) i18n 集成（next-intl）
- 在现有 `next-intl` 架构下，新增统一的文案键位，如：
  - `common.toast.createSuccess` / `common.toast.createFail`
  - `common.toast.updateSuccess` / `common.toast.updateFail`
  - `common.toast.deleteSuccess` / `common.toast.deleteFail`
- 按语言维护到 `web/src/i18n/messages/{locale}/common.json`。
- 页面/组件中通过 `useTranslations("common")` 获取，并传给 `withToast`。

### 6) 业务接入（以学生管理为例）
- 在创建/更新/删除等操作中，使用 `withToast` 包裹调用 `apiFetch` 的 Promise。
- 成功时显示成功文案；失败时显示来自后端的 `message` 或兜底错误文案；完成后按需刷新列表或路由。

### 7) UX 与可访问性
- 默认自动关闭，支持手动关闭按钮；错误消息保留更长时间（如 5-7s）。
- 避免重复堆叠：同一操作短时间内的重复错误可合并或去抖。
- 屏幕阅读器可读（`sonner` 已内置无障碍考量）。
- 不提供“复制错误 ID/追踪 ID”的动作。

## 影响范围
- 新增 Provider 组件与两个基础库文件：
  - `web/src/providers/NotificationProvider.tsx`
  - `web/src/lib/api-client.ts`
  - `web/src/lib/withToast.ts`
- 需要在 `web/src/app/layout.tsx` 中引入 Provider。
- 业务模块（如学生管理）在“创建/更新/删除”时调用 `withToast` 包裹请求。
- i18n 文案文件新增/更新对应 `common.toast.*` 键位。

## 验收标准
- 创建/更新/删除学生：成功/失败均能出现对应通知，文案多语言正确。
- 后端返回标准错误（`message`）时，通知能显示该错误摘要（后端响应统一为 `code/message/data`）。
- 网络错误或异常断网时，显示通用失败通知；不出现未捕获异常。
- 通知在所有页面均可用，不影响 SSR，首屏无报错。
- 通知样式统一、位置一致、自动关闭与手动关闭均可用。

## 待讨论事项
1. 国际化文案键位与默认文案内容确认。
2. Provider 在布局中的具体插入位置与顺序（与 `Navbar` 的相对位置）。
3. 错误消息映射细则（仅 `message`，为空时的兜底文案与多语言处理）。
4. 通知时长与位置的默认设定是否需要环境区分（如开发/生产）。

---
实施建议顺序：
1) 引入 `sonner` 与 `NotificationProvider`；2) 增加 `api-client` 与 `withToast`；3) 在学生管理 CRUD 接入；4) 补齐 i18n 文案与基于 `message` 的错误映射细则。
