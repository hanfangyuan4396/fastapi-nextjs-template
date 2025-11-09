# FastAPI + PostgreSQL 异步化重构（需求文档）

## 需求描述
当前后端（FastAPI）使用 SQLAlchemy 同步会话（`Session`）访问数据库，并通过 `run_in_threadpool` 在路由层包裹阻塞查询。这种方式会带来线程池切换开销、难以充分利用 asyncio 并发能力，且在高并发或 I/O 密集场景下吞吐受限。需要将数据库访问改造为原生异步（`AsyncEngine` + `AsyncSession`），消除线程池包装，落实 FastAPI + PostgreSQL 的异步最佳实践。

## 需求目标
- 将数据库访问改造为基于 SQLAlchemy 2.x 的异步访问栈（`AsyncEngine`/`AsyncSession`）。
- 移除控制器层的 `run_in_threadpool` 包装，端到端异步。
- 维持现有 API 契约与业务行为（返回结构、校验逻辑、错误码）不变。
- 提升在 I/O 密集负载下的吞吐与并发能力，降低 P95 响应时间。
- 保证观测性、可回滚、可灰度发布。

## 技术方案（最佳实践）

### 选型
- ORM 与会话：SQLAlchemy >= 2.0（原生 async API）。
- 驱动：使用 `psycopg3` 异步驱动（`postgresql+psycopg_async://`）。
  - 理由：持续维护、与 SQLAlchemy 2.x 贴合、生态成熟。
- 连接池：使用 SQLAlchemy 内置连接池（无 PgBouncer 前提）。
- 迁移：Alembic（保留原流程，不强制改造）。

### 架构改造概览
1) 应用生命周期与依赖注入
- 在现有数据库初始化位置，将同步引擎与会话改造为 `AsyncEngine` 与 `async_sessionmaker(class_=AsyncSession)`，不新增文件。
- 现有依赖注入保持形式不变，但改造为异步 `yield` 出单请求范围的 `AsyncSession`，并采用 `async with session.begin()` 控制事务。

2) 路由（Controller）层
- 移除 `run_in_threadpool`，路由保持 `async def`，直接 `await` 调用 service。
- 保留 RBAC/鉴权依赖不变；所有需要 DB 的依赖改用 `AsyncSession`。

3) Service/Repository 层
- 将方法签名改为异步（`async def`），接受 `AsyncSession`。
- 查询采用 SQLAlchemy 2.x 的 `select()`/`insert()`/`update()`/`delete()` 与 `await session.execute(...)`。
- 读操作尽量使用 `scalars()`/`scalar_one()`；写操作置于 `async with session.begin():` 事务块中；必要时手动 `await session.flush()`。
- 分页查询采用 `select(Model).order_by(...).offset(...).limit(...)`；计数使用 `select(func.count(...))`，避免对全量 `Query.count()` 的隐式陷阱。

4) 模型与模式迁移
- ORM 模型基本不变；若当前为声明性映射（Declarative），可直接复用。
- Alembic 继续维护迁移脚本，运行仍使用同步引擎连接（Alembic 默认支持）；亦可配置异步运行（可选）。

### 连接管理与池化（PostgreSQL 最佳实践）
- 连接 URL（示例，psycopg3 async）：
  - `postgresql+psycopg_async://user:pass@host:5432/dbname`
- 引擎参数：尽量与当前同步连接池参数保持一致（如 `pool_size`、`max_overflow`、`pool_recycle`、`pool_pre_ping` 等），如当前未配置则沿用 SQLAlchemy 默认值；仅在 psycopg3 需要时新增 `connect_args`（例如合理的 `statement_timeout`）。

### 事务与一致性
- 以「短事务」为原则，避免在事务中做网络 I/O。
- 严格在 `async with session.begin()` 中进行写操作；读操作默认非事务，若有一致性要求可启用 REPEATABLE READ 并限时。
- 并发竞争策略：
  - 基于唯一约束 + 捕获异常（幂等写入）。
  - 需要排他时可使用 `with_for_update(skip_locked=True)` 实现任务抢占。
- 大批量写入采用批处理并显式 `flush`，避免事务过大。

### 错误处理与超时
- 统一捕获 SQL 异常，映射为统一错误码（维持现状语义）。
- 在业务层设置「数据库操作级」超时（如 3~5s），并结合 PostgreSQL `statement_timeout` 双保险。
- 对外仅暴露业务语义，隐藏底层数据库错误细节（安全）。

### 可观测性与诊断
- SQLAlchemy 日志：在本地与预发开启 `echo=False` + `pool_logging`；错误路径附带 `query_id`。
- Tracing：OpenTelemetry（FastAPI + SQLAlchemy instrumentation），打点关键 DB 调用，产出慢查询分布。
- 关键指标：连接池使用率、等待时间、错误率、P95/P99 RT、超时计数。

### 本地开发与测试
- 单元测试：引入 `pytest-asyncio`；使用 sqlite 进行功能验证（不引入 PostgreSQL 测试）。
- 集成与性能测试：本阶段不进行 PostgreSQL 集成测试与压力测试，仅验证功能正确性。

### 兼容与迁移策略
- 本期范围仅改造 students 模块为异步数据库访问，直接在现有实现上重构（不新增并行的异步实现或新文件）。
- 路由移除 `run_in_threadpool`，端到端异步；其他模块暂保持不变，后续再行推广。
- 保持 API 契约不变；不引入双栈灰度。

### 安全与合规
- 连接串不落盘，统一从环境变量注入（K8s Secret/平台密钥）。
- 权限最小化：只授予应用所需 schema 权限。
- 审计：开启数据库审计日志（按合规要求）。

## 影响面
- 基础设施：数据库初始化、依赖注入、应用生命周期。
- 控制器：路由函数签名与调用方式（移除 `run_in_threadpool`）。
- Service/Repository：方法签名与查询方式改为异步。
- 测试：异步测试工具链与夹具（fixtures）。
- 监控：新增异步 SQL tracing 指标。

## 交付物
- 重构后的数据库连接初始化（在现有位置原地改造为异步，使用 psycopg3）。
- 学生模块（controller + service）端到端异步，接口不变。
- 文档：运行手册与参数说明（连接池、超时）。

## 验收标准
- 功能：现有 API 行为、返回结构、错误码完全一致（回归全部通过）。
- 架构：控制器不再使用 `run_in_threadpool`，Service 改为异步，并通过 `AsyncSession` 访问数据库。
- 代码质量：无阻塞点混入（禁止在异步路径中调用同步 DB）；lint/typecheck 通过。
