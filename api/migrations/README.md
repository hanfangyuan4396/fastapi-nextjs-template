Alembic migrations for FastAPI/SQLAlchemy.

# 前置要求

## 安装依赖
确保已安装alembic：
```bash
pip install alembic
```

## 工作目录
所有迁移操作都需要在 `api/migrations/` 目录下执行：
```bash
cd api/migrations
```

# 数据库表结构修改规范

## 1. 基本原则

- **禁止直接在数据库修改表结构**：所有数据库表结构的变更必须通过修改模型定义和使用迁移脚本完成，严禁直接在数据库中执行DDL语句修改表结构。
- **保持模型与数据库同步**：确保代码中的模型定义始终与实际数据库结构一致。
- **迁移脚本作为历史记录**：所有结构变更都应通过迁移脚本记录，并且要提交迁移脚本到github，方便回溯和审计。
- **检查迁移脚本**：仔细检查自动生成的upgrade()和downgrade()函数是否完全符合预期，尤其是其中包含删除表结构时，必要时手动修改迁移脚本，确保正确性和完整性。

## 2. 表结构修改流程

### 2.1. 同步最新代码和迁移脚本

```bash
git switch main  # 切换到main分支
git pull # 拉取最新代码
alembic upgrade head  # 确保本地数据库是最新状态
git switch -c xxx  # 创建并切换到新的开发分支
```

### 2.2. 修改模型定义

在相应的models文件中更新数据库模型定义，如添加字段、修改关系等。

### 2.3. 生成迁移脚本

#### 2.3.1. 自动生成迁移脚本（推荐）

基于 ORM 自动对比生成，适用于标准的表结构变更：

```bash
alembic revision --autogenerate -m "简要描述此次变更内容"
```

#### 2.3.2. 手动创建空迁移脚本

适用于需要执行复杂数据迁移、原生SQL操作或特殊需求时：

```bash
alembic revision -m "简要描述此次变更内容"
```

**注意**：手动创建的迁移脚本中 `upgrade()` 和 `downgrade()` 函数为空，需要手动编写具体的数据库操作代码。

### 2.4. 检查迁移脚本

- 打开生成的迁移脚本文件（位于 `api/migrations/versions/` 目录）
- 仔细检查自动生成的upgrade()和downgrade()函数是否完全符合预期
- 必要时手动修改迁移脚本，确保正确性和完整性
- 特别注意数据类型转换和可能的数据丢失风险

### 2.5. 执行迁移脚本

```bash
alembic upgrade head
```

### 2.6. 验证变更

- 检查开发数据库表结构是否已按预期更新
- 运行相关功能测试，确保应用正常工作
- 提交代码并创建合并请求
- 代码合并后关注CI/CD，测试环境会自动执行迁移，验证迁移是否成功

## 3. 注意事项

### 3.1. bin/boot.sh 中迁移的执行

在 `api/bin/boot.sh` 中，迁移的执行通过 `MIGRATION_ENABLED` 环境变量控制（默认 true），在启动 FastAPI 之前自动执行 Alembic 迁移。

```bash
# 检查是否启用自动迁移
MIGRATION_ENABLED=${MIGRATION_ENABLED:-"true"}
if [[ "${MIGRATION_ENABLED}" == "true" ]]; then
  echo "Running migrations"
  pushd "$(dirname "$0")/../migrations" > /dev/null
  alembic upgrade head
  popd > /dev/null
fi
```

### 3.2. 共享开发环境数据库的问题

目前提供了共享的开发环境数据库，但是如果需要修改表结构，使用共享的开发环境数据库，会存在以下问题：

- **并发修改冲突**：多人同时修改表结构可能导致冲突，某些迁移可能会覆盖或破坏其他人的修改
- **迁移顺序不确定**：在共享数据库上，不同开发者执行迁移的顺序无法保证，可能导致数据库状态不一致
- **开发中断**：一个开发者的表结构变更可能会影响其他开发者的功能开发和测试

所以在需要修改表结构时，建议使用本地数据库进行开发和测试。

1. 快速创建本地开发数据库数据

可通过把测试服务器的测试数据库数据拷贝到本地，快速创建本地开发数据库数据

2. 启动本地数据库服务

3. 配置api/.env 文件

在api/.env 文件中，配置数据库连接信息
```bash
# PostgreSQL database configuration
DB_USERNAME=postgres                  # PostgreSQL用户名
DB_PASSWORD=postgres                  # PostgreSQL密码
DB_HOST=localhost                     # PostgreSQL主机地址
DB_PORT=35432                         # PostgreSQL主端口
DB_DATABASE=fastapi-nextjs            # PostgreSQL数据库
```

### 3.3. 多人数据库迁移合并策略

#### 3.3.1. 规范Git工作流

- **采用特性分支模式**：
  - 每个人在自己的特性分支上开发
  - 完成后通过PR/MR合并到主分支
  - 代码审查必须包括数据库迁移审查

- **及时合并主分支**：
  - 经常将主分支合并到特性分支
  - 这样可以尽早发现和解决迁移冲突

#### 3.3.2. 处理冲突的具体步骤

1. **当两人修改同一表时**：

   - **合并代码**：先合并模型代码（models.py）
   - **检查迁移依赖**：确认迁移文件的依赖链正确
   - **解决冲突**：
     ```bash
     # 获取所有头部版本
     alembic heads

     # 合并多个头部版本（将所有 head 合并为一条）
     alembic merge -m "merge migrations" heads
     # 或合并特定版本
     alembic merge -m "merge migrations" 版本号1 版本号2
     ```

2. **冲突解决示例**：

   假设Alice和Bob都创建了迁移：
   - Alice: `a123_add_column_x.py`（添加字段x）
   - Bob: `b456_add_column_y.py`（添加字段y）

   当合并代码时:
   ```bash
   # 合并后会看到两个头部版本
   alembic heads
   # 输出: a123 (head), b456 (head)

   # 创建合并迁移
   alembic merge -m "merge migrations" a123 b456
   # 这会创建一个新的迁移文件,仅包含依赖关系,不包含实际操作

   # 应用所有迁移
   alembic upgrade head
   ```

3. **合并后的验证**：
   - 合并迁移创建后，必须在本地开发环境验证
   - 检查数据库表结构是否包含所有期望的变更
   - 确认应用程序能正确访问所有新增或修改的字段
   - 如果合并后出现问题，可使用 `alembic downgrade` 回滚

#### 3.3.3. 不同类型迁移的处理策略

1. **添加表或列**：
   - 最安全的操作，通常不会引起冲突
   - 可以同时进行并合并迁移

   **实践案例**：处理两个基于同一父版本的迁移脚本
   ```
   情景：两个迁移脚本(add_plan.py和add_whatsapp.py)都基于同一父版本c6b22a9f202f创建，
   add_whatsapp.py已经执行了迁移，而add_plan.py还未执行。两个迁移都是添加新表且没有关联。

   解决方法：
   1. 修改add_plan.py的down_revision，指向已执行的add_whatsapp.py的revision ID：
      # 原来的
      down_revision = 'c6b22a9f202f'

      # 修改为
      down_revision = '6bbce37aa301'  # add_whatsapp.py的revision ID

   2. 不需要改变add_plan.py中的其他内容，因为两个迁移都是添加新表，不会有冲突
   3. 修改完成后执行add_plan.py的迁移

   这种方法确保了迁移链的正确性，形成一个线性的迁移历史，同时由于两个迁移都是添加新表且没有关联，
   这种调整不会影响数据库的完整性。
   ```

2. **修改列属性**：
   - 需要特别小心，尤其是类型变更
   - 考虑分两步完成：先添加新列，再迁移数据并删除旧列
   - 必须考虑数据转换和默认值问题

3. **删除表或列**：
   - 高风险操作，可能影响现有功能
   - 应先将列标记为废弃，确认无影响后再删除
   - 考虑保留数据的备份策略

4. **重命名操作**：
   - Flask-Migrate/Alembic通常将重命名识别为"删除+添加"
   - 手动修改迁移脚本，使用正确的重命名操作
   - 确保引用该列的所有代码都已更新

#### 3.3.4. 版本回滚策略

- **编写完善的downgrade函数**：
  - 每个upgrade操作必须有对应的downgrade
  - 回滚操作应当完全恢复原始状态
  - 测试回滚功能确保可用

- **回滚指定版本**：
  ```bash
  # 回滚到特定版本
  alembic downgrade 版本号

  # 回滚最近的一个迁移
  alembic downgrade -1
  ```

#### 3.3.5. 处理特殊情况

- **重置极端情况**：
  - 如果迁移历史彻底混乱，可考虑重置
  - 需要删除 api/migrations/versions 目录下所有迁移文件
  - 删除开发/测试/生产数据库的 alembic_version 表
  - 重新执行 `revision --autogenerate` 与 `upgrade head`
    ```bash
    alembic revision --autogenerate -m "reset init"
    alembic upgrade head
    ```
  - 注意：生产环境重置风险极高，应谨慎评估

- **脱离版本控制的变更处理**：
  - 发现数据库被直接修改时，可创建空迁移或使用 stamp 记录当前状态
  - 使用 `alembic stamp` 将数据库标记为特定版本
    ```bash
    alembic stamp 版本号
    ```
  - 从此版本继续维护迁移历史

- **手动修复依赖链**：
  - 必要时直接编辑迁移文件修正 `down_revision`

---

附：配置说明（与 Alembic 集成）

- 迁移目录：`api/migrations/`（包含 `alembic.ini`、`env.py`、`script.py.mako`、`versions/`）
- 连接配置：`env.py` 使用 `utils.config.Settings` 读取 `DB_USERNAME/DB_PASSWORD/DB_HOST/DB_PORT/DB_DATABASE` 组装数据库 URL
- 环境变量示例：见 `api/.env.example`
