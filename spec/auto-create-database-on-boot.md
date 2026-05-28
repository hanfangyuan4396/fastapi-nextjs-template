# 启动时自动创建数据库

## 需求描述

当前 Docker 首次启动时，PostgreSQL 容器可能只初始化默认维护库，没有创建应用配置中的 `DB_DATABASE`。此时 API 启动脚本继续执行 Alembic 迁移会因为目标数据库不存在而失败。

## 需求目标

- 增加一个后端启动前脚本：当 `DB_DATABASE` 指定的数据库不存在时自动创建。
- 将数据库创建步骤接入 `api/bin/boot.sh`，并确保执行顺序早于 Alembic 迁移。
- 在 `docker/docker-compose.yaml` 中增加开关配置，默认开启。
- 脚本需要保持幂等：数据库已存在时不修改现有数据库。

## 技术方案

- 新增 `api/scripts/ensure_database.py`，使用当前环境变量中的 `DB_USERNAME`、`DB_PASSWORD`、`DB_HOST`、`DB_PORT`、`DB_DATABASE` 连接 PostgreSQL 维护库。
- 将默认管理员初始化脚本从 `api/utils/seed_users.py` 移动到 `api/scripts/seed_users.py`，与启动/维护类脚本统一放在 `scripts` 目录。
- 默认维护库为 `postgres`，可通过 `DB_MAINTENANCE_DATABASE` 覆盖。
- 新增启动开关 `INIT_DATABASE_ENABLED`，在 `boot.sh` 中默认关闭，Docker Compose 中默认设置为开启。
- `api/bin/boot.sh` 中的脚本入口更新为 `python -m scripts.ensure_database` 和 `python -m scripts.seed_users`。
- 执行顺序：创建数据库 -> Alembic 迁移 -> 初始化默认管理员 -> 启动 API。

## 待讨论事项

- 是否需要在非 Docker 部署中也默认开启 `INIT_DATABASE_ENABLED`。
- 是否需要把 `DB_MAINTENANCE_DATABASE` 补充到 `.env.example` 中作为显式可配置项。
