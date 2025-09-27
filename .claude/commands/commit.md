# Commit Full code commit workflow: review, branch, commit, PR link
/commit

# Description
执行完整的代码提交流程，包括查看变动、创建新分支、提交代码并提供PR链接

# 分支命名规范
- `feature/功能描述` - 新功能开发
- `bugfix/问题描述` - Bug修复
- `hotfix/紧急修复描述` - 紧急修复
- `docs/文档描述` - 文档更新
- `refactor/任务描述` - 重构
- `chore/任务描述` - 杂项任务

注意分支前缀不能使用"fix"/"feat"

# Commit Log 规范
格式：`前缀(目录名): 描述`
- `feat(目录名): 描述` - 新功能
- `fix(目录名): 描述` - Bug修复
- `docs(目录名): 描述` - 文档更新
- `refactor(目录名): 描述` - 代码重构
- `chore(目录名): 描述` - 杂项任务
- `ci(目录名): 描述` - CI/CD相关

**目录名规范**：
- `api` - Python Flask 后端
- `web` - Next.js 前端
- `core` - 核心业务逻辑
- `services` - 业务服务层
- `models` - 数据库模型
- `controllers` - API 控制器
- `docker` - Docker 配置
- `docs` - 项目文档
- 其他具体目录名

# Execution
1. 执行`git status` 和 `git diff`查看此次代码变动，对于新增文件，可以查看文件内容
2. 根据变动类型和上述命名规范创建新的分支名
3. 如果当前分支是main分支，需要切换到新分支：`git checkout -b [新分支名]`
4. 添加所有变更：`git add .`
5. 创建有意义的提交信息并提交：`git commit -m "[提交信息]"`
6. pre-commit hook会自动调整代码格式，如果修改文件后，需要重新执行`git add .`和`git commit -m "[提交信息]"`，不应添加`--amend`参数，因为之前的commit并未成功执行
7. 无法自动调整的代码格式，需要你手动调整
8. 推送分支到远程：`git push -u origin [新分支名]`
9. 使用gh命令检查PR是否存在，如果不存在则创建PR

# Notes
- 分支名应该反映变更的内容和目的
- 提交信息应该简洁明了地描述变更
- 当pre-commit hook修改文件后，需要重新执行`git add .`和`git commit -m "[提交信息]"`，不应使用`--amend`参数，因为之前的commit并未成功执行
