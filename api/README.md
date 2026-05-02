# fastapi nextjs api

一个简单的 FastAPI 应用程序，用于演示基本的 Web API 功能。

## 快速开始

### 安装依赖

```bash
uv sync
```

### 运行应用

#### 方法1：直接运行Python文件
```bash
uv run python app.py
```


应用将在 `http://localhost:8000` 启动。

### 交互式文档

启动应用后，可以访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 开发

使用 `--reload` 参数可以在代码更改时自动重启服务器。

### Ruff 使用（代码规范与格式化）

建议在 `api/` 目录执行以下命令。

检查（仅报告问题）：

```bash
uv run ruff check .
```

自动修复并格式化：

```bash
uv run ruff check . --fix && uv run ruff format .
```

仅格式化：

```bash
uv run ruff format .
```

### pre-commit（代码质量检查）

安装 Git 钩子并预下载所有检查工具（推荐）：

```bash
uv run pre-commit install --install-hooks
```

> **说明**：
> - 使用 `--install-hooks` 参数会预先下载所有检查工具，确保每次 commit 都能快速执行
> - Ruff 钩子仅作用于 `api/` 目录
> - 文件格式修复钩子（去除尾部空格、文件末尾换行等）作用于全仓库

对全仓库运行一遍钩子（验证配置）：

```bash
uv run pre-commit run --all-files
```

手动运行特定钩子：

```bash
# 只运行 ruff 检查
uv run pre-commit run ruff-check --all-files

# 只运行代码格式化
uv run pre-commit run ruff-format --all-files
```

### pytest（单元测试）

```bash
uv run pytest # api目录下执行
```
