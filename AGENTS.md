# Repository Guidelines

## 项目结构与模块组织
- `api/` 为 FastAPI 后端，`controllers/` 存放路由控制器，`services/` 处理业务逻辑，`models/` 为 SQLAlchemy 模型，`schemas/` 为 Pydantic 模型，`tests/` 为 pytest 测试。迁移文件在 `api/migrations/`。
- `web/` 为 Next.js 应用，App Router 在 `web/src/app/`，共享工具在 `web/src/lib/`，API 封装在 `web/src/service/`。
- `docker/` 包含 `docker-compose.yaml`、服务脚本与挂载配置，例如 `docker/volumes/api/.env`。
- `spec/` 存放前端与编码规范相关的说明文档。

## 构建、测试与开发命令
后端（除非另有说明，从仓库根目录执行）：
- `pip install -r api/requirements.txt` 安装 Python 依赖。
- `python api/app.py` 启动 API，访问 `http://localhost:8000`。
- `pytest`（在 `api/` 目录执行）运行后端测试。
- `ruff check .` / `ruff format .`（在 `api/` 目录执行）进行 lint 与格式化。

前端：
- `cd web && npm install` 安装依赖。
- `cd web && npm run dev` 启动 Next.js 开发服务器。
- `cd web && npm run build` 构建生产资源。
- `cd web && npm run lint` 运行 ESLint。

Docker：
- `cd docker && ./fastapi-nextjs-service.sh start` 通过 Compose 启动全栈服务。

## 编码风格与命名规范
- Python：4 空格缩进，Ruff 格式化，行宽 120，双引号（见 `api/.ruff.toml`）。
- TypeScript/React：2 空格缩进，遵循 Next.js + ESLint 默认规则（`web/eslint.config.mjs`）。
- 命名：Python 模块/函数使用 snake_case，React 组件使用 PascalCase，已有文件名保持 kebab-case 风格。

## 测试指南
- 后端测试位于 `api/tests/`，使用 pytest。需要时添加 `@pytest.mark.unit` 或 `@pytest.mark.integration`。
- 前端测试使用 Vitest，测试文件放在 `web/src/` 下，命名为 `*.test.ts` 或 `*.test.tsx`。
- `cd web && npm run test` 单次运行，`npm run test:coverage` 输出覆盖率。

## 提交与合并请求规范
- Commit 历史遵循 Conventional Commits，并可带 scope（如 `feat(web): add students flow`、`fix(ci): update workflow`）。保持简短、动词开头。
- PR 需要清晰描述，相关问题请关联链接；涉及 UI 变更请附截图；如有迁移或环境改动请注明。

## 配置与安全建议
- 后端配置通过环境变量加载，示例见 `docker/volumes/api/.env`。
- 避免提交密钥，使用本地 `.env` 或 CI secrets。

## 重要，必须遵守的规则
- 请使用中文回答我的提问
- 循序渐进写代码，实现一部分代码停下来总结一下你的代码，方便我及时review
- python环境路径为 /home/hfy/miniconda3/envs/xxx/bin/python，使用此环境执行python测试、数据库迁移等操作
- 执行测试时需要在api目录下执行pytest命令
- 使用命令创建alembic迁移脚本，不要直接生成：alembic revision --autogenerate -m "简要描述此次变更内容"，并且要cd api/migrations目录下执行命令
- 对于后端代码，要执行ruff和pytest命令，确保代码质量
- 对于前端代码，要执行lint、test、build命令，确保代码质量

## 拆分与验证流程（前端）
- 拆分思路：先识别 UI 区块与逻辑边界，UI 抽成独立组件，业务/状态逻辑抽成 hooks
- 拆分过程：先抽 UI 组件，再抽 hooks；组件保持 props 清晰、逻辑不外泄；对话框类组件可拆为“壳 + 表单”
- 测试补充：为新组件/新 hooks 增加最小可用的单测（渲染态/关键行为），必要时补环境标记（如 happy-dom）
- 质量保障：每次拆分后立即运行 `npm run lint`、`npm run test`、`npm run build`
- 问题修复：出现 error/warning 时优先修复（类型、依赖数组、测试环境、构建类型兼容等），确保三项命令全绿
