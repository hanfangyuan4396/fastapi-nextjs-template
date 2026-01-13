# fastapi-nextjs-template

![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/hanfangyuan4396/fastapi-nextjs-template?utm_source=oss&utm_medium=github&utm_campaign=hanfangyuan4396%2Ffastapi-nextjs-template&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)

### 项目简介

一个开箱即用的全栈模板：后端基于 FastAPI + SQLAlchemy + PostgreSQL，前端基于 Next.js(App Router) + React + TypeScript + Tailwind CSS。内置示例「学生管理」含列表与新增，支持 Docker 一键编排，适合作为中小型项目或学习实践的起点。

### 技术栈

- **后端（api）**: FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, Psycopg 3, Uvicorn, Python 3.12
- **前端（web）**: Next.js 16, React 19, TypeScript 5, Tailwind CSS 4, next-intl, react-hook-form, shadcn/ui
- **数据库**: PostgreSQL
- **容器/编排**: Docker, Docker Compose（含 Nginx 反向代理）
- **质量与工具**: Pytest, Ruff, ESLint, Vitest, Testing Library, MSW, happy-dom, GitHub Actions
- **认证与鉴权**: 基于 JWT 的认证与依赖注入式鉴权（含角色控制）

### 目录结构

```text
.
├─ api/                      # 后端服务（FastAPI）
│  ├─ app.py                 # 应用入口，装配路由与中间件
│  ├─ controllers/           # 路由控制器（接口层）
│  │  ├─ echo_controller.py
│  │  └─ students_controller.py
│  ├─ services/              # 业务服务层
│  │  └─ students_service.py
│  ├─ core/                  # 认证/鉴权与安全核心层（Token、认证依赖、授权）
│  ├─ models/                # 数据模型（SQLAlchemy）
│  │  ├─ base.py
│  │  └─ students.py
│  ├─ schemas/               # 请求/响应模型（Pydantic）
│  │  └─ students.py
│  ├─ utils/                 # 配置、日志、数据库等工具
│  │  ├─ config.py
│  │  ├─ db.py
│  │  ├─ db_url.py
│  │  ├─ error_handlers.py
│  │  └─ logging.py
│  ├─ migrations/            # 数据库迁移（Alembic）
│  ├─ tests/                 # 单元测试
│  ├─ Dockerfile
│  └─ requirements.txt
│
├─ web/                      # 前端应用（Next.js）
│  ├─ src/
│  │  ├─ app/                # App Router 入口与页面
│  │  │  ├─ layout.tsx
│  │  │  ├─ page.tsx
│  │  │  └─ students/        # 学生管理页面示例
│  │  │     ├─ page.tsx
│  │  │     ├─ students-client.tsx
│  │  │     └─ students-create-dialog.tsx
│  │  ├─ service/            # 与后端交互的 HTTP 封装
│  │  │  ├─ http.ts
│  │  │  └─ students.ts
│  │  ├─ i18n/               # 国际化配置（next-intl）
│  │  ├─ lib/                # 前端通用工具
│  │  └─ proxy.ts
│  ├─ tests/                 # 前端测试（Vitest + Testing Library）
│  ├─ public/
│  ├─ Dockerfile
│  ├─ package.json
│  ├─ next.config.ts
│  └─ tsconfig.json
│
├─ docker/                   # 本地/生产编排与脚本
│  ├─ docker-compose.yaml    # 编排 api/web/postgres/nginx
│  ├─ fastapi-nextjs-service.sh
│  └─ volumes/               # 持久化与配置挂载
│     ├─ api/.env            # 后端环境变量示例（通过挂载提供）
│     ├─ postgres/data/      # 数据持久化目录
│     └─ nginx/              # Nginx 配置
│        ├─ nginx.conf
│        └─ conf.d/
│
├─ spec/                     # spec coding document
│  ├─ frontend-i18n.md
│  ├─ frontend-student-management.md
│  └─ spec-rules.md
│
├─ .github/                  # GitHub 配置与工作流
│  └─ workflows/             # CI/CD 工作流
│     ├─ only-build.yaml     # PR/非 main 分支：检测变更并本地构建 API/Web 镜像（不推送）
│     ├─ api-tests.yaml      # API 目录变更触发 Pytest，生成覆盖率摘要
│     ├─ style.yaml          # 变更范围触发 Ruff(后端)/ESLint(前端) 风格检查
│     ├─ build-push.yaml     # main/tag 推送：构建并推送 API/Web 镜像到 ACR
│     └─ deploy.yaml         # 构建成功后通过 SSH 脚本触发部署
├─ .claude/                  # Claude 配置
│  └─ commands/              # Claude 本地命令
│     ├─ commit.md           # 代码提交命令
│     └─ review.md           # 代码审查命令
└─ README.md
```

### 测试

- 后端：在 `api/` 目录执行 `pytest`
- 前端：在 `web/` 目录执行 `npm run test`（覆盖率：`npm run test:coverage`）

### GitHub Actions 变量与 Secrets 表

| 名称                   | 类型      | 作用范围 / Workflow | 是否必填 | 默认值                                                     | 说明                                   |
|------------------------|-----------|----------------------|----------|------------------------------------------------------------|----------------------------------------|
| `ALIYUN_REGISTRY_USER` | Secret    | `build-push.yaml`   | 是       | 无                                                         | 阿里云镜像仓库登录用户名。             |
| `ALIYUN_REGISTRY_PWD`  | Secret    | `build-push.yaml`   | 是       | 无                                                         | 阿里云镜像仓库登录密码 / Access Key。  |
| `ALIYUN_REGISTRY`      | Variable  | `build-push.yaml`   | 否       | `registry.cn-hangzhou.aliyuncs.com`                        | 镜像仓库地址（含 region）。            |
| `PROJ_API_IMAGE_NAME`  | Variable  | `build-push.yaml`   | 否       | `hanfangyuan/fastapi-nextjs-api`                                  | API 镜像名称（不含 registry）。        |
| `PROJ_WEB_IMAGE_NAME`  | Variable  | `build-push.yaml`   | 否       | `hanfangyuan/fastapi-nextjs-web`                                  | Web 镜像名称（不含 registry）。        |
| `SERVER_SSH_USER`      | Secret    | `deploy.yaml`       | 是       | 无                                                         | 目标服务器 SSH 用户名。                |
| `SERVER_SSH_KEY`       | Secret    | `deploy.yaml`       | 是       | 无                                                         | 目标服务器 SSH 私钥。                  |
| `SERVER_SSH_HOST`      | Variable  | `deploy.yaml`       | 推荐     | 无                                                         | 目标服务器主机名或 IP。                |
| `SERVER_SSH_SCRIPT`    | Variable  | `deploy.yaml`       | 否       | `cd services/fastapi-nextjs-template/docker && ./fastapi-nextjs-service.sh start && docker image prune -af` | 在服务器上执行的部署脚本命令。         |

### Deploy（`deploy.yaml`）SSH 前置准备（避免握手失败）

`deploy.yaml` 使用 `appleboy/ssh-action` 通过 **SSH 私钥** 登录服务器执行部署脚本。为避免 SSH 握手失败，请确保在服务器上将对应的 **公钥** 添加到目标用户的 `~/.ssh/authorized_keys`。

```bash
mkdir -p ~/.ssh
cat >> ~/.ssh/authorized_keys << 'EOF'
# 粘贴公钥内容（通常是 *.pub 文件里的那一行）
EOF
```
