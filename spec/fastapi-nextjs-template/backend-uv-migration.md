# 后端 Python 依赖管理迁移到 uv 需求文档

## 需求描述
当前后端 Python 依赖通过 `api/requirements.txt` 与 `pip install -r requirements.txt` 管理，本地开发、Docker 构建、测试、Ruff、Alembic 迁移等命令也直接依赖系统 Python 或已激活环境。需要将后端 Python 管理统一迁移到 `uv`，让依赖安装、命令执行、锁文件、Docker 构建和文档说明保持一致，降低环境漂移与 CI/Docker 复现成本。

## 需求目标
- 后端依赖改为由 `uv` 管理，明确 Python 版本、运行依赖、开发依赖与锁文件。
- 本地开发命令统一通过 `uv run` 执行，避免依赖用户手动激活虚拟环境。
- Docker 构建同步使用 `uv` 安装依赖，并尽量利用锁文件保证可复现构建。
- 后端测试、Ruff、Alembic 迁移、默认管理员初始化等命令同步更新为 `uv run ...`。
- README、AGENTS、迁移说明等文档同步替换旧的 `pip`/裸 `python`/裸 `pytest` 命令。
- 保持现有 FastAPI 应用行为、测试语义、Docker Compose 启动方式不变。

## 技术方案

### 依赖文件调整
- 在 `api/` 下新增 `pyproject.toml`，声明：
  - `requires-python = ">=3.12,<3.13"` 或与现有 Docker 基础镜像一致的 Python 版本约束。
  - 运行依赖：从 `api/requirements.txt` 迁移现有业务依赖。
  - 开发依赖：`pytest`、`pytest-asyncio`、`pytest-mock`、`pytest-cov`、`ruff`、`pre-commit` 等开发工具。
- 生成并提交 `api/uv.lock`，作为本地、CI、Docker 的依赖锁定依据。
- 删除 `api/requirements.txt`，完全切换到 `pyproject.toml + uv.lock`，避免出现两套依赖来源。
- 将 `pre-commit` 放入开发依赖组，并统一通过 `uv run pre-commit ...` 执行。

### 本地开发命令
- 安装/同步依赖：
  ```bash
  cd api && uv sync
  ```
- 启动 API：
  ```bash
  cd api && uv run python app.py
  ```
- Ruff 检查与格式化：
  ```bash
  cd api && uv run ruff check .
  cd api && uv run ruff format .
  ```
- 后端测试：
  ```bash
  cd api && uv run pytest
  ```
- Alembic 自动迁移脚本生成：
  ```bash
  cd api/migrations && uv run alembic revision --autogenerate -m "简要描述此次变更内容"
  ```
- 执行迁移：
  ```bash
  cd api/migrations && uv run alembic upgrade head
  ```

### Docker 调整
- `api/Dockerfile` 改为安装并使用 `uv`：
  - 复制 `pyproject.toml` 与 `uv.lock`。
  - 使用 `uv sync --frozen --no-dev` 安装生产依赖到镜像内 `.venv`。
  - 将 `.venv/bin` 加入 `PATH`，运行阶段直接使用虚拟环境中的 `python`、`uvicorn`、`alembic` 等命令。
  - 使用多阶段构建，`builder` 阶段使用 uv 生成 `.venv`，`runtime` 阶段只复制 `.venv` 与应用代码。
  - 再复制应用代码，提升 Docker layer 缓存命中率。
- 启动脚本 `api/bin/boot.sh` 在 Docker 镜像中直接使用已同步环境的可执行文件，不在容器启动阶段依赖 `uv run`。
- `uv` 主要作为构建期依赖同步工具，不作为生产容器的启动入口。
- Docker Compose 入口与环境变量保持不变，`cd docker && ./fastapi-nextjs-service.sh start` 继续可用。

### 测试与质量保障
- 后端变更后，在 `api/` 目录执行：
  ```bash
  uv run ruff check .
  uv run ruff format --check .
  uv run pytest
  ```
- Docker 验证：
  ```bash
  docker build -f api/Dockerfile api
  cd docker && ./fastapi-nextjs-service.sh start
  ```

### CI 同步范围
- `.github/workflows/api-tests.yaml` 当前存在后端 Python 测试流程：
  - `actions/setup-python@v5` 使用 Python 3.12。
  - 缓存类型为 `pip`，缓存依赖文件为 `api/requirements.txt`。
  - 依赖安装命令为 `pip install -r requirements.txt`。
  - 测试与覆盖率命令为 `python -m pytest ...`、`python -m coverage ...`。
  - 需要改为安装/启用 `uv`，缓存 `uv` 目录，以 `api/uv.lock` 作为缓存/触发依据，并使用 `uv sync --frozen`、`uv run pytest ...`、`uv run coverage ...`。
- `.github/workflows/style.yaml` 当前存在后端 Ruff 流程：
  - `actions/setup-python@v5` 使用 Python 3.12。
  - 安装命令为 `pip install ruff==0.12.8`。
  - 检查命令为裸 `ruff check ./api` 与 `ruff format --check ./api`。
  - 需要改为 `uv sync --frozen` 后执行 `uv run ruff check ./api` 与 `uv run ruff format --check ./api`，或在 `api/` 工作目录执行 `uv run ruff check .`。
- `.github/workflows/only-build.yaml` 与 `.github/workflows/build-push.yaml` 均会构建 `api/Dockerfile`：
  - Dockerfile 改为 uv 后，这两个流程会自动覆盖 Docker 构建验证。
  - path filter 需要包含 `api/pyproject.toml` 与 `api/uv.lock`。
  - 删除 `api/requirements.txt` 后，需要移除旧的 `api/requirements.txt` 触发项。
- 所有 workflow 中出现的 `api/requirements.txt` 触发条件、pip 缓存、pip 安装命令都需要同步替换。

### 文档同步范围
- 根目录 `README.md`：后端安装、启动、测试命令。
- `api/README.md`：快速开始、Ruff、pytest、pre-commit 命令。
- `api/migrations/README.md`：Alembic 安装、生成、升级、回滚命令。
- `AGENTS.md`：后端构建、测试、迁移与重要规则中的 Python 环境说明。
- CI/部署文档中出现的 `pip install -r api/requirements.txt`、`python api/app.py`、裸 `pytest`、裸 `ruff` 命令。

## 影响面
- 后端依赖入口从 `requirements.txt` 切换到 `pyproject.toml + uv.lock`。
- 删除 `api/requirements.txt`，CI、Docker、文档不再引用该文件。
- Docker 构建流程改变，镜像内保留 `.venv`；服务端口、启动脚本、Compose 服务名不变。
- 本地开发和测试命令需要切换到 `uv`。
- Alembic 迁移流程保持目录要求不变，只是命令前缀改为 `uv run`。

## 已实现改动（同步记录）
- 新增 `api/pyproject.toml` 与 `api/uv.lock`，删除 `api/requirements.txt`。
- `api/Dockerfile` 改为多阶段构建：builder 使用 uv 同步生产依赖到 `.venv`，runtime 只复制 `.venv` 和应用代码。
- 新增 `api/.dockerignore`，避免 `.venv`、缓存和本地环境文件进入 Docker 构建上下文。
- GitHub Actions 后端测试与 Ruff 流程改为 `astral-sh/setup-uv`、`uv sync --frozen`、`uv run ...`。
- API Docker 构建相关 workflow 的 path filter 同步包含 `api/pyproject.toml` 与 `api/uv.lock`。
- 根 README、`api/README.md`、`api/migrations/README.md`、`AGENTS.md` 已同步 uv 命令。

## 验收标准
- `cd api && uv sync --frozen` 成功。
- `cd api && uv run ruff check .` 通过。
- `cd api && uv run ruff format --check .` 通过。
- `cd api && uv run pytest` 通过。
- `docker build -f api/Dockerfile api` 成功。
- `cd docker && ./fastapi-nextjs-service.sh start` 后 API 能正常启动并执行迁移/初始化逻辑。
- GitHub Actions 中 API Tests、API Ruff Style、API Docker build 流程均切换到 uv 后通过。
- 文档、CI、Docker 中不再引用 `api/requirements.txt`。

## 待讨论事项
- 暂无。
