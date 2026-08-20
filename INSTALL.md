# youzi-init-project 安装 / 卸载 / 更新 / 使用指南

> 推荐使用 [`./install.sh`](#一install-一键脚本推荐) 一键安装。如需手工操作，请参考 [二、手工安装](#二手工安装)。

---

## 一、install.sh 一键脚本（推荐）

仓库自带 `install.sh`，一条命令完成安装 / 卸载 / 更新 / 状态查询。

### 1.1 一键安装

```bash
cd /Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project
./install.sh install
```

按提示确认后，会创建 `~/.claude/skills/youzi-init-project` 符号链接。

### 1.2 一键查看状态

```bash
./install.sh status
```

输出当前安装状态、关键文件检查、环境检查（python3 / jinja2）。

### 1.3 一键卸载

```bash
./install.sh uninstall
```

### 1.4 一键更新

符号链接模式下，源目录任何修改都会即时生效，无需 update。复制模式下需要：

```bash
./install.sh update
```

### 1.5 高级选项

```bash
# 安装到自定义目录
./install.sh install --dir ~/my-skills

# 复制模式（适合无法创建符号链接的环境）
./install.sh install --mode copy

# 查看所有选项
./install.sh help
```

### 1.6 安装流程

脚本会自动完成：

1. 验证源目录（含 SKILL.md）
2. 创建 `~/.claude/skills/`
3. 选择安装方式（link / copy）
4. 创建符号链接或复制文件
5. 显示下一步指引

---

## 二、手工安装

如不便运行 `install.sh`，可手工操作。

### 2.1 符号链接（推荐）

```bash
mkdir -p ~/.claude/skills
ln -s /Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project \
      ~/.claude/skills/youzi-init-project
```

### 2.2 直接复制

```bash
cp -r /Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project \
      ~/.claude/skills/youzi-init-project
```

### 2.3 从 git 仓库安装

```bash
git clone https://github.com/your-org/youzi-init-project.git \
            ~/.claude/skills/youzi-init-project
```

### 安装后验证

```bash
ls ~/.claude/skills/youzi-init-project/SKILL.md
# 重启 Claude Code，在对话中输入
/yz:init-admin --help
```

---

## 三、卸载

### 用脚本

```bash
./install.sh uninstall
```

### 手工

```bash
rm -rf ~/.claude/skills/youzi-init-project
```

---

## 四、更新

### 符号链接模式

直接编辑源目录，重启 Claude Code 即可生效（SKILL.md 在启动时读取一次）。

### 复制模式

```bash
# 用脚本
./install.sh update

# 或手工
rm -rf ~/.claude/skills/youzi-init-project
cp -r /Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project \
      ~/.claude/skills/youzi-init-project
```

---

## 五、使用

### 5.1 命令一览

| 命令                     | 范围                                                 | 典型场景                   |
| ------------------------ | ---------------------------------------------------- | -------------------------- |
| `/yz:init-admin <name>`  | 后端 + 前端 + 中间件 + **数据库自动维护** + 本地调试 | 新建一套完整管理系统       |
| `/yz:init-server <name>` | 纯后端 + 中间件 + **数据库自动维护** + 本地调试      | 新增/替换一个后端 API 工程 |
| `/yz:init-ui <name>`     | 纯前端 + 本地调试                                    | 新增/替换一个前端工程      |

### 5.2 使用步骤

1. **在 Claude Code 对话框中输入命令**

   ```
   /yz:init-admin my-admin
   ```

2. **回答交互式问题**（Claude 通过 AskUserQuestion 收集选项）
   - 数据库类型？
   - 是否启用 RabbitMQ / MinIO / Celery？
   - 是否初始化 git？

3. **等待生成完成**
   - Claude 调用 `scripts/init.py` 渲染模板
   - 输出 `<项目名>/` 目录
   - 在对话中打印启动指引

4. **按指引启动**

   ```bash
   cd my-admin
   make start          # 启动中间件
   make backend-dev    # 终端 A：后端
   make frontend-dev   # 终端 B：前端
   ```

### 5.3 直接用脚本（不通过 Claude Code）

```bash
# 完整前后端
python3 /Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project/scripts/init.py my-admin

# 后端 + 中间件
python3 /Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project/scripts/init.py my-api --only server

# 仅前端
python3 /Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project/scripts/init.py my-web --only ui

# 高级选项
python3 /Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project/scripts/init.py data-platform \
  --only admin \
  --database mysql \
  --enable-redis \
  --enable-rabbitmq \
  --enable-celery \
  --enable-minio \
  --init-git
```

### 5.4 各模式启动指引

**admin 模式**：

```bash
cd my-admin
make start          # 启动 PostgreSQL + Redis + ...
make backend-dev    # 终端 A：启动后端（http://localhost:8000）
make frontend-dev   # 终端 B：启动前端（http://localhost:5173）
```

**server 模式**：

```bash
cd my-api
make start          # 启动中间件
make install        # 安装后端依赖
make backend-dev    # 启动 FastAPI 开发服务器
```

**ui 模式**：

```bash
cd my-web
pnpm install        # 或 npm install
pnpm dev            # 启动开发服务器
```

### 5.5 数据库自动维护（亮点）

所有含后端的模式（admin / server）启动时会**自动维护表结构**：

| 状态     | 行为                                                         |
| -------- | ------------------------------------------------------------ |
| 首次启动 | 自动 `create_all` 建表 + `alembic stamp head` + 插入种子数据 |
| 后续启动 | 自动 `alembic upgrade head` + 插入缺失的种子数据             |
| 任何失败 | 记录警告但不阻塞启动                                         |

可通过 `.env` 中的开关关闭：

```env
AUTO_CREATE_TABLES=true   # 首次启动自动建表
AUTO_MIGRATE=true         # 后续启动自动迁移
AUTO_SEED_DATA=true       # 自动插入种子数据
```

### 5.6 数据库维护命令

```bash
make db-migrate msg="add xxx"   # 自动生成迁移
make db-upgrade                  # 应用迁移
make db-downgrade                # 回滚
make db-reset                    # 重置数据库
make db-shell                    # 进入 psql
make db-backup                   # 备份
make db-restore FILE=xxx.sql     # 恢复
```

---

## 六、常见问题

### Q1: 修改了 SKILL.md 但命令没生效

**A**: 重启 Claude Code。SKILL.md 在启动时读取一次。

### Q2: 修改了 templates/ 但生成的项目没变

**A**: 模板渲染时直接从 `templates/` 读取，无需重启 Claude Code。但要注意：之前已经生成的项目不会自动更新。

### Q3: 想让 Skill 全局可用（任意目录都能调用）

**A**: 必须放在 `~/.claude/skills/` 下，项目级别的 `.claude/skills/` 只在该项目内生效。

### Q4: 多个项目使用同一个 Skill

**A**: 用符号链接最方便，所有项目共享同一个 Skill 副本。

### Q5: 升级 Skill 后旧的脚手架项目能用吗

**A**: 可以。Skill 只是生成器，旧项目独立运行。但新项目会包含新功能（如数据库自动维护）。

### Q6: 如何调试 Skill 本身

**A**:

```bash
# 用 status 检查安装和环境
./install.sh status

# 直接跑脚本看输出
python3 ~/.claude/skills/youzi-init-project/scripts/init.py test --init-git

# 检查 SKILL.md 格式是否正确（YAML frontmatter 必须合法）
head -5 ~/.claude/skills/youzi-init-project/SKILL.md
```

### Q7: Skill 安装位置一览

| 位置                               | 范围       | 优先级         |
| ---------------------------------- | ---------- | -------------- |
| `~/.claude/skills/<name>/`         | 全局       | 低             |
| `<project>/.claude/skills/<name>/` | 仅当前项目 | 高（覆盖全局） |

### Q8: 生成的 .env 没生效 / 后端启动失败

**A**: 检查 `.env` 中 `SECRET_KEY` 是否设置（init.py 会自动生成）。同时确认 `.env` 文件位置：

- admin 模式：`backend/.env`
- server 模式：项目根目录 `.env`

---

## 七、推荐工作流

```bash
# 1. 一次性安装（一行命令搞定）
cd /Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project
./install.sh install

# 2. 平时开发：直接编辑本地仓库
# 修改 templates/、SKILL.md、scripts/init.py ...

# 3. 测试改动
python3 scripts/init.py test-project
# 检查 test-project/ 的内容

# 4. 在 Claude Code 中使用
/yz:init-admin my-real-project

# 5. 当需要发布给团队时
cd /Users/zhangpeng/workspace/liaohe/youzi/youzi-init-project
git add . && git commit -m "feat: update scaffold"
git push origin main

# 团队成员安装
git clone https://github.com/your-org/youzi-init-project.git
cd youzi-init-project
./install.sh install
```

---

## 八、仓库目录结构

```
youzi-init-project/
├── SKILL.md              # Skill 描述（/yz:* 触发词）
├── README.md             # 项目总览
├── INSTALL.md            # 本文档：安装/卸载/更新/使用
├── install.sh            # 一键安装脚本
├── scripts/
│   └── init.py           # 模板渲染脚本
├── templates/
│   ├── backend/          # 后端模板
│   ├── frontend/         # 前端模板
│   └── root/             # 根级中间件 + 文档
└── examples/             # 示例项目
```

## 九、许可证

MIT
