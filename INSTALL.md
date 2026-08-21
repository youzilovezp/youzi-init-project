# 安装 / 卸载 / 更新 / 使用参考

> README 已经覆盖了快速上手。本文档面向需要深入了解安装与运维的用户。

---

## 一、安装

### 1.1 一键安装（推荐）

```bash
cd /path/to/youzi-init-project
./install.sh install
```

脚本会自动完成：

1. 验证源目录（含 `templates/skills/*/SKILL.md`）
2. 创建 `~/.claude/skills/`
3. 逐个安装三个 skill：`yz-init-admin` / `yz-init-server` / `yz-init-ui`
4. 共享 `scripts/` 和 `templates/`（符号链接，修改源仓库即时生效）

### 1.2 高级选项

```bash
./install.sh install --dir ~/my-skills   # 自定义安装目录
./install.sh install --mode copy         # 复制模式（不创建符号链接）
./install.sh help                        # 查看所有选项
```

### 1.3 手工安装（不推荐）

```bash
SKILL_SRC=/path/to/youzi-init-project
mkdir -p ~/.claude/skills/{yz-init-admin,yz-init-server,yz-init-ui}

# 复制每个 SKILL.md
cp $SKILL_SRC/templates/skills/admin/SKILL.md  ~/.claude/skills/yz-init-admin/SKILL.md
cp $SKILL_SRC/templates/skills/server/SKILL.md ~/.claude/skills/yz-init-server/SKILL.md
cp $SKILL_SRC/templates/skills/ui/SKILL.md     ~/.claude/skills/yz-init-ui/SKILL.md

# 共享 scripts 和 templates
for s in yz-init-admin yz-init-server yz-init-ui; do
  ln -s $SKILL_SRC/scripts   ~/.claude/skills/$s/scripts
  ln -s $SKILL_SRC/templates ~/.claude/skills/$s/templates
done
```

### 1.4 从 git 仓库安装

```bash
git clone https://github.com/your-org/youzi-init-project.git
cd youzi-init-project
./install.sh install
```

---

## 二、卸载

### 用脚本

```bash
./install.sh uninstall
```

### 手工

```bash
rm -rf ~/.claude/skills/yz-init-{admin,server,ui}
```

---

## 三、更新

**符号链接模式（默认）**：直接编辑源目录，重启 Claude Code 即可生效。无需 update。

**复制模式**：

```bash
./install.sh update
```

---

## 四、命令一览

Claude Code 中会显示三个独立命令：

| 命令                     | 范围                                             | 典型场景               |
| ------------------------ | ------------------------------------------------ | ---------------------- |
| `/yz-init-admin <name>`  | 后端 + 前端 + 中间件 + 数据库自动维护 + 本地调试 | 新建一套完整管理系统   |
| `/yz-init-server <name>` | 后端 + 中间件 + 数据库自动维护 + 本地调试        | 新增/替换后端 API 工程 |
| `/yz-init-ui <name>`     | 纯前端 + 本地调试                                | 新增/替换前端工程      |

> Claude Code 不支持 `:` 作为命令字符，所以三个独立 skill 用 `-` 分隔。

### 使用流程

1. **输入命令**：`/yz-init-admin my-app`
2. **回答对话中的问题**（数据库类型、中间件选项等）
3. **等待生成**：skill 调用 `scripts/init.py` 渲染模板，输出 `my-app/` 目录
4. **启动项目**：

```bash
cd my-app
make start          # 启动中间件
make backend-dev    # 终端 A
make frontend-dev   # 终端 B
```

### 直接用脚本（不通过 Claude Code）

```bash
python3 /path/to/youzi-init-project/scripts/init.py my-admin
python3 /path/to/youzi-init-project/scripts/init.py my-api --only server
python3 /path/to/youzi-init-project/scripts/init.py my-web --only ui
```

### 各模式启动指引

| 模式   | 启动                                                 |
| ------ | ---------------------------------------------------- |
| admin  | `make backend-dev` + `make frontend-dev`（两个终端） |
| server | `make backend-dev`                                   |
| ui     | `pnpm dev`                                           |

### 数据库自动维护

admin / server 模式启动时**自动维护表结构**：

| 状态     | 行为                                                |
| -------- | --------------------------------------------------- |
| 首次启动 | `create_all` 建表 + `alembic stamp head` + 种子数据 |
| 后续启动 | `alembic upgrade head` + 缺失的种子数据             |
| 失败     | 记录警告但不阻塞启动                                |

可用 `.env` 中的 `AUTO_CREATE_TABLES` / `AUTO_MIGRATE` / `AUTO_SEED_DATA` 关闭。

### 数据库维护命令

```bash
make db-migrate msg="add xxx"   # 生成迁移
make db-upgrade                  # 应用迁移
make db-downgrade                # 回滚
make db-reset                    # 重置数据库
make db-shell                    # 进入 psql
make db-backup                   # 备份
make db-restore FILE=xxx.sql     # 恢复
```

---

## 五、常见问题

### Q1: 三个 skill 命令在 Claude Code 中看不到？

检查 `~/.claude/skills/` 下有 `yz-init-admin`、`yz-init-server`、`yz-init-ui` 三个目录，每个含 `SKILL.md`。缺失则重跑 `./install.sh install`，最后重启 Claude Code。

### Q2: 修改了 SKILL.md 但命令没生效？

SKILL.md 在 Claude Code 启动时读取一次，需重启 Claude Code。修改 `templates/` 不需要重启。

### Q3: 后端启动失败 / .env 没生效？

检查 `.env` 中 `SECRET_KEY` 是否设置（init.py 会自动生成）。位置：

- admin 模式：`backend/.env`
- server 模式：项目根目录 `.env`

### Q4: 多个项目如何共享这个 Skill？

符号链接模式天然支持：所有项目共享 `~/.claude/skills/yz-init-*`。修改源仓库对所有生效。

### Q5: 生产环境要注意什么？

1. 修改默认账号 `youzi` / `youzi@123456`
2. 用 `openssl rand -hex 32` 生成新的 `SECRET_KEY`
3. 关闭 `DEBUG` 和 `DB_ECHO`
4. `LOG_FORMAT` 改为 `json` 便于日志聚合
5. `CORS_ORIGINS` 只保留可信域名

---

## 六、许可证

MIT
