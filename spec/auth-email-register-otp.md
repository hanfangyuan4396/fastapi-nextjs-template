## 需求描述

- 为当前项目（FastAPI + Next.js，已采用 JWT + 刷新令牌、RBAC）增加**注册功能**：
  - 用户通过 **邮箱注册账号**，不允许直接设置为已激活状态。
  - 注册时先提交邮箱 → 服务端发送一次性验证码（OTP）邮件 → 用户填写验证码完成验证后，才允许设置密码并创建账号。
  - 只允许已验证邮箱的用户成功创建 `users` 记录，并分配默认角色（普通用户 `user`）。
- 该注册流程需要与现有鉴权方案（`/auth/login`, `/auth/refresh`, RBAC）兼容，不破坏已有登录/刷新逻辑。

## 需求目标

- **安全的邮箱注册流程**
  - 通过邮箱 + 验证码确认邮箱归属，避免垃圾/恶意注册。
  - 验证码具有过期时间与错误次数限制，防止暴力穷举。
- **良好的用户体验**
  - 前端提供完整的注册页：输入邮箱 → 收验证码 → 填写验证码 → 设置密码 → 注册成功 → 自动登录或跳转登录页。
  - 对错误情况（验证码错误/过期、邮箱已注册等）提供明确的错误提示。
- **与现有体系兼容**
  - 注册成功后可沿用现有 `/auth/login` 流程获得 `access_token` + 刷新令牌，当前方案采用“注册即登录”：注册接口成功后直接返回 `access_token` 并设置 `refresh_token` Cookie。
  - 新注册用户默认角色为 `user`，仅可访问普通用户权限范围（例如查看学生）。
- **可扩展性**
  - 验证码发送与验证逻辑可复用到未来的“找回密码/重置密码”功能。
  - 邮件发送抽象为独立模块，但当前仅支持使用 SMTP 协议发送邮箱验证码，暂不考虑替换不同邮件服务商和测试环境假发件方案。

## 技术方案（初稿）

### 1) 接口设计（后端）

- **发送验证码**：`POST /auth/register/send-code`
  - 入参：`email`。
  - 行为：
    - 校验邮箱格式。
    - 若该邮箱已被注册（存在 `users` 记录且 `is_active=true`），返回错误（如：409 `EMAIL_ALREADY_REGISTERED`）。
    - 生成一次性验证码（固定为 6 位数字）。
    - 将验证码及其元数据（邮箱、过期时间、尝试次数、请求 IP 等）存储在 Redis 中。
    - 通过邮件服务发送验证码邮件（内容可配置，包含验证码及有效期说明）。
    - 对同一邮箱/同一 IP 做发送频率限制（例如每分钟 1 次，每小时 N 次上限）。
  - 出参：操作结果（不返回验证码本身），如 `{ "success": true }`。

- **校验验证码并完成注册**：`POST /auth/register/verify-and-create`
  - 入参：`email`, `code`, `password`（后续可扩展昵称等字段；邮箱即用户名，不再单独输入用户名字段）。
  - 行为：
    - 校验邮箱格式与密码复杂度。
    - 根据邮箱从 Redis 查询最近一次有效验证码记录：
      - 若不存在、已过期、已使用、错误次数超限或处于黑名单则返回错误（如：400/422 不同错误码）。
    - 验证用户提交的 `code` 是否匹配（Redis 中仅保存验证码哈希，比较时对用户提交的 `code` 进行相同算法哈希后再比对）：
      - 不匹配：增加该验证码记录的错误计数，超过阈值后将其置为失效。
    - 匹配成功：
      - 标记该验证码记录为已使用（通过删除对应的 Redis key 实现）。
      - 再次检查该邮箱是否已经有激活用户（防并发/竞态）。
      - 创建新 `users` 记录：
        - `username`：直接使用邮箱作为用户名（邮箱即用户名，不再新增单独的 `email` 字段）。
        - `password_hash`：使用现有 `hash_password` 工具。
        - `role`：默认 `user`。
        - `is_active`：true。
        - 其他字段：`failed_login_attempts=0`, `lock_until=NULL`, `token_version=1` 等。
      - 注册成功后直接返回 `access_token` 并设置 `refresh_token` Cookie（实现“注册即登录”），前端可直接跳转首页或学生页面。

### 2) 数据模型与存储

- **验证码存储（Redis）**
  - 使用 Redis 存储验证码及其元数据，建议使用统一的 key 前缀（例如：`auth:email_verification:{scene}:{email}`）。
  - Redis 中可存储字段包括（可采用 Hash 结构）：
    - `code_hash`：验证码哈希（对 6 位数字验证码进行加盐哈希后保存，避免明文存储）。
    - `scene`：使用场景（如 `register`，未来可扩展 `reset_password` 等）。
    - `created_at`：创建时间。
    - `used`：是否已使用。
    - `failed_attempts`：失败次数。
    - `max_attempts`：最大允许失败次数（如 5）。
    - `ip`、`user_agent`：可选，辅助风控。
  - 通过 Redis TTL 自动过期，不需要额外的定期清理任务，也不单独持久化过期时间字段。

- **与现有 `users` 表关系**
  - 注册完成后才写入 `users`。
  - 现有登录/鉴权逻辑无需修改，只需确保新用户数据满足既有约束（其中 `users.username` 直接使用邮箱，即邮箱即登录名）。

### 3) 邮件发送与配置

- **邮件发送模块**
  - 在 `api/utils/email.py`（或类似路径）中封装发送函数 `send_verification_email(email, code, expires_in_minutes)`。
  - 邮件发送服务仅支持 SMTP 协议，不再抽象为支持多邮件服务商的可插拔实现。

- **配置项**
  - `.env` 中新增或约定以下专用于邮箱验证码场景的配置项：
    - `EMAIL_VERIFICATION_FROM`：发送方邮箱（邮箱验证码专用）。
    - `EMAIL_VERIFICATION_SMTP_HOST`：用于发送验证码邮件的 SMTP 服务器主机名。
    - `EMAIL_VERIFICATION_SMTP_PORT`：用于发送验证码邮件的 SMTP 服务器端口。
    - `EMAIL_VERIFICATION_SMTP_USER`：用于发送验证码邮件的 SMTP 登录用户名。
    - `EMAIL_VERIFICATION_SMTP_PASSWORD`：用于发送验证码邮件的 SMTP 登录密码。
    - `EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES`：验证码有效期（例如 10 分钟）。
  - 发送频控相关参数（如每邮箱/每 IP 的时间窗口与上限）通过应用配置文件（如 `config.py`）中的常量控制，例如：
    - `EMAIL_VERIFICATION_RATE_LIMIT_PER_EMAIL`
    - `EMAIL_VERIFICATION_RATE_LIMIT_PER_IP`
    这些常量在代码中提供合理的默认值，无需用户在 `.env` 中显式配置，以避免配置项过多带来的压力。

### 4) 前端交互流程（Next.js）

- **注册页 UI**
  - 步骤一：输入邮箱，点击“发送验证码”
    - 调用 `POST /auth/register/send-code`。
    - 成功后提示“验证码已发送，请查收邮件”，并进入输入验证码与密码的步骤。
  - 步骤二：输入收到的验证码 + 设置密码
    - 调用 `POST /auth/register/verify-and-create`。
    - 成功后：
      - 注册成功即自动登录：后端返回 `access_token` 并设置 `refresh_token` Cookie，前端直接跳转首页或学生页面。
      - （预留）如需改为“注册成功后手动登录”流程，可由前端引导用户跳转至登录页。
  - 错误处理：
    - 展示后端返回的错误信息，如“邮箱已注册”、“验证码错误/过期”、“发送过于频繁”等。

- **与 JWT / RBAC 的关系**
  - 注册完成 → 用户通过 `/auth/login` 获得 `access_token` 与 `refresh_token`。
  - 新用户的 `role='user'`，在前端导航与路由守卫中按普通用户处理：
    - 可访问：`students`。
    - 不可访问：`students-management`（由 RBAC 与前端 `RequireRole` 限制）。

## 安全与风控要求

- **验证码安全**
  - 验证码长度与复杂度：固定为 6 位数字。
  - 过期时间：例如 5 分钟，过期后必须拒绝使用（通过 Redis TTL 控制，无需单独持久化过期时间字段）。
  - 单个验证码错误次数上限（如 5 次），超限后作废，并可临时禁止该邮箱/该 IP 重复尝试。
  - 验证码在 Redis 中以加盐哈希形式存储，避免 Redis 数据泄露时直接暴露验证码明文。

- **发送频率控制**
  - 同一邮箱在短时间内不得频繁请求验证码（例如 60 秒内只允许发送一次），具体阈值通过 `EMAIL_VERIFICATION_RATE_LIMIT_PER_EMAIL` 控制。
  - 同一 IP 也需要频控，防止大规模滥用接口，具体阈值通过 `EMAIL_VERIFICATION_RATE_LIMIT_PER_IP` 控制。

- **与账号锁定策略协同**
  - 注册阶段不计入登录失败次数，不影响现有“30分钟内连续失败5次锁定1小时”的登录策略。
  - 后续若基于注册行为进行风控（如同一 IP 大量注册），可在日志与审计中增加标记。

## 已确认设计点

- **注册成功后的行为**
  - 采用“注册即登录”：注册接口成功后直接返回 `access_token` 并设置 `refresh_token` Cookie。
- **验证码存储方式**
  - 使用 Redis 存储验证码及其元数据，验证码以加盐哈希形式保存，不新增数据库表。
- **邮箱是否作为唯一登录名**
  - 邮箱即用户名：`users.username` 字段直接存储邮箱，不再单独引入 `email` 字段。
- **邮件服务落地方案**
  - 仅使用支持 SMTP 协议的邮箱服务发送验证码邮件，暂不考虑第三方邮件服务商 SDK 或测试环境假发件方案。
