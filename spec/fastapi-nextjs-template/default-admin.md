# 默认管理员账号初始化需求文档

## 需求描述
项目初始化时需要自动创建一个默认的管理员账号与密码，确保系统在首次部署/启动后即可登录后台进行基础配置与管理。同时需要避免重复创建以及不必要的明文密码持久化风险。

## 需求目标
- 在项目初始化阶段自动创建默认管理员账号。
- 默认管理员账号只创建一次；若已存在同名管理员账号则不更新密码。
- 管理员账号与密码通过环境变量配置，避免写死在代码中。
- 初始化逻辑由独立开关控制，便于不同环境选择是否执行。
- 记录必要的初始化结果（成功/已存在/失败），便于排查。

## 技术方案
- 在启动脚本中读取环境变量并触发初始化逻辑。
- 环境变量：
  - `DEFAULT_ADMIN_USERNAME`
  - `DEFAULT_ADMIN_PASSWORD`
  - `INIT_ADMIN_ENABLED`（独立开关，`true` 时执行初始化，默认 `false`）
- 初始化逻辑：
  - 查询用户表是否已存在同名账号；若存在则跳过，不更新密码。
  - 若不存在，使用安全哈希写入数据库，角色设置为 `admin`，`is_active` 为 `true`。
- 日志中不输出完整密码，仅提示已读取配置。
- 初始化脚本可参考现有 `api/utils/seed_users.py`（可复用哈希与用户创建逻辑，保持“仅创建不更新密码”的行为）。
- `api/utils/seed_users.py` 提供 `create_user_if_missing`，仅创建用户并在已存在时直接跳过。

## 已实现改动（同步记录）
- 启动脚本：`api/bin/boot.sh` 在 `INIT_ADMIN_ENABLED=true` 时执行 `python -m utils.seed_users`，失败会阻断启动。
- 初始化脚本：`api/utils/seed_users.py` 仅支持从环境变量创建默认管理员，不再包含 dev/test 默认账号逻辑。
- 用户创建函数：将 `upsert_user` 重命名为 `create_user_if_missing`，只创建不更新。
- Docker Compose：`docker/docker-compose.yaml` 的 `api` 服务加入 `INIT_ADMIN_ENABLED`。
- 环境变量示例：`api/.env.example` 增加 `DEFAULT_ADMIN_USERNAME`、`DEFAULT_ADMIN_PASSWORD`。
- 测试用例：`api/tests/unit_tests/test_seed_users.py` 调整为“只创建、已存在跳过”语义。

## 待讨论事项
- 初始化失败时应阻断启动（明确要求）。
- 生产环境不强制设置 `INIT_ADMIN_ENABLED=true`（明确要求）。
