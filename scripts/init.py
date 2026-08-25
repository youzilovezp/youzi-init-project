#!/usr/bin/env python3
"""
scaffold-init 初始化脚本。

设计原则：给非技术人员使用——CLI 越简单越好。
    python scripts/init.py my-app                  # 默认 admin 模式（前后端 + PostgreSQL）
    python scripts/init.py my-app --only ui        # 仅前端
    python scripts/init.py my-app --only server    # 仅后端
    python scripts/init.py my-app --with-redis     # 启用 Redis（生产多 worker 场景）

中间件策略：make start 优先复用本机已运行的 PostgreSQL/Redis，缺的才用 Docker 起。
数据库 / 端口全部走 .env 或默认值。

完整文档见 templates/skills/<mode>/SKILL.md。
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError:
    print("缺少 jinja2（仅后端模板需要），请执行：pip install jinja2")
    sys.exit(1)


def warn(msg: str) -> None:
    """统一警告输出（黄字 emoji 前缀）。"""
    print(f"  ⚠️  {msg}", file=sys.stderr)


# ---------- 默认值（业界惯例；非技术人员看一眼就懂） ----------
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_PORT = 3000
DEFAULT_POSTGRES_PORT = 5432
DEFAULT_REDIS_PORT = 6379


# ---------- Jinja context ----------
def build_context(args: argparse.Namespace) -> dict:
    return {
        "project_name": args.project_name,
        "project_title": args.project_title,
        "secret_key": secrets.token_hex(32),
        "only": args.only,
        # Redis 默认关：限流/黑名单走进程内内存；--with-redis 启用（生产多 worker 场景）
        "enable_redis": args.with_redis,
        "backend_port": DEFAULT_BACKEND_PORT,
        "frontend_port": DEFAULT_FRONTEND_PORT,
        "postgres_port": DEFAULT_POSTGRES_PORT,
        "redis_port": DEFAULT_REDIS_PORT,
        "admin_user": args.admin_user,
        "admin_pass": args.admin_pass,
        "admin_email": DEFAULT_ADMIN_EMAIL,
        "db_password": secrets.token_urlsafe(20),
        "redis_password": secrets.token_urlsafe(20),
    }


# ---------- Jinja rendering ----------
def render_template(
    src: Path, dst: Path, env: Environment, context: dict, search_path: Path
) -> None:
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for child in src.iterdir():
            render_template(child, dst / child.name, env, context, search_path)
        return

    if src.suffix == ".tmpl":
        rel = str(src.relative_to(search_path))
        target_path: Path = dst.with_suffix("")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        template = env.get_template(rel)
        target_path.write_text(template.render(**context), encoding="utf-8")
        return

    # 非 .tmpl 文件——纯拷贝（保护 frontend 的 Vue/TS/HTML 中的 {{ }}）
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def generate_admin(
    target_dir: Path, env: Environment, context: dict, templates_dir: Path
) -> None:
    print("📦 模式：admin（完整前后端 + 中间件）")
    render_template(
        templates_dir / "backend", target_dir / "backend", env, context, templates_dir
    )
    render_template(
        templates_dir / "frontend", target_dir / "frontend", env, context, templates_dir
    )
    render_template(templates_dir / "root", target_dir, env, context, templates_dir)


def generate_ui(
    target_dir: Path, env: Environment, context: dict, templates_dir: Path
) -> None:
    print("📦 模式：ui（仅前端）")
    render_template(templates_dir / "frontend", target_dir, env, context, templates_dir)
    # 单独渲染根 .gitignore.tmpl（带 {% if only == 'admin' %} 条件，确保 ui-only 模式也有干净的根 .gitignore）
    env.get_template("root/.gitignore.tmpl").stream(**context).dump(
        str(target_dir / ".gitignore")
    )


def generate_server(
    target_dir: Path, env: Environment, context: dict, templates_dir: Path
) -> None:
    """server 模式：后端在项目根（与 SKILL.md 描述一致）。"""
    print("📦 模式：server（后端 + 中间件）")
    render_template(templates_dir / "backend", target_dir, env, context, templates_dir)
    render_template(templates_dir / "root", target_dir, env, context, templates_dir)


GENERATORS = {"admin": generate_admin, "ui": generate_ui, "server": generate_server}


# ---------- Frontend post-processing ----------
PLACEHOLDER_FRONTEND = "Youzi Admin"
PLACEHOLDER_BACKEND_PORT_DEFAULT = str(DEFAULT_BACKEND_PORT)
PLACEHOLDER_FRONTEND_PORT_DEFAULT = str(DEFAULT_FRONTEND_PORT)


def post_process_frontend(target_dir: Path, context: dict) -> None:
    """前端里写死的占位符与默认端口，纯文本替换。"""
    title = context["project_title"]
    backend_port = str(context["backend_port"])
    frontend_port = str(context["frontend_port"])
    project_name = context["project_name"]

    targets = [
        target_dir / "src" / "config" / "index.ts",
        target_dir / ".env.development",
        target_dir / ".env.production",
        target_dir / "src" / "views" / "login" / "index.vue",
        target_dir / "src" / "layouts" / "BasicLayout.vue",
        target_dir / "index.html",
        target_dir / "vite.config.ts",
        target_dir / "前端说明.md",
        target_dir / "docs" / "架构说明.md",
        target_dir / "docs" / "配置说明.md",
        target_dir / "docs" / "开发指南.md",
        target_dir / "docs" / "技术栈.md",
    ]

    for f in targets:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        text = text.replace(PLACEHOLDER_FRONTEND, title)
        text = text.replace(
            f"localhost:{PLACEHOLDER_BACKEND_PORT_DEFAULT}", f"localhost:{backend_port}"
        )
        text = text.replace(
            f"localhost:{PLACEHOLDER_FRONTEND_PORT_DEFAULT}",
            f"localhost:{frontend_port}",
        )
        if f.name == "vite.config.ts":
            text = text.replace(
                f"port: {PLACEHOLDER_FRONTEND_PORT_DEFAULT}",
                f"port: {frontend_port}",
            )
        f.write_text(text, encoding="utf-8")

    pkg = target_dir / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            data["name"] = f"{project_name}-frontend"
            data["description"] = f"{title} 前端"
            pkg.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except Exception as exc:
            print(f"⚠️ 跳过 package.json: {exc}", file=sys.stderr)


# ---------- .env 写入 ----------
def write_dotenv(
    target: Path,
    env_example: Path,
    ctx: dict,
) -> None:
    """把 .env.example 渲染后写入 .env，用真实密码替换所有占位符。

    之前只替换 SECRET_KEY → POSTGRES_PASSWORD 等仍是 CHANGE_ME_* 占位符，
    用户 .env 拿不到真实密码，启动必失败。

    之后：同时确保 .env / .env.* 被 .gitignore 排除（admin 模式：项目根；
    server 模式：target_dir 根）。
    """
    content = env_example.read_text(encoding="utf-8")
    # 替换规则:CHANGE_ME_XXX 占位符 → ctx 对应字段
    replacements = {
        "__SECRET_KEY__": ctx["secret_key"],
        "CHANGE_ME_DB_PASSWORD": ctx["db_password"],
        "CHANGE_ME_REDIS_PASSWORD": ctx["redis_password"],
        "CHANGE_ME_TO_RANDOM_PASSWORD": ctx["admin_pass"],
    }
    # 长 key 先替换(避免 CHANGE_ME_TO_RANDOM_PASSWORD 被 CHANGE_ME_DB 之类先吃掉)
    for placeholder, real in sorted(replacements.items(), key=lambda x: -len(x[0])):
        content = content.replace(placeholder, real)
    target.write_text(content, encoding="utf-8")

    # 确保 .env / .env.* 被 .gitignore 排除
    # admin 模式：target = target_dir/backend/.env → 项目根 .gitignore
    # server 模式：target = target_dir/.env → 项目根 .gitignore（同样位置）
    gitignore = (
        target.parent.parent / ".gitignore"
        if target.parent.name == "backend"
        else target.parent / ".gitignore"
    )
    if gitignore.exists():
        gi = gitignore.read_text(encoding="utf-8")
        if ".env" not in gi.splitlines():
            gitignore.write_text(
                gi.rstrip() + "\n.env\n.env.*\n!.env.example\n", encoding="utf-8"
            )


def init_git_safely(target_dir: Path) -> None:
    """git init + git add .，.env 由 .gitignore 自动忽略。"""
    # git 未安装时给出友好提示，而不是抛 FileNotFoundError traceback
    if not shutil.which("git"):
        warn("git 未安装，跳过 --init-git（不影响项目生成）")
        return
    try:
        r = subprocess.run(
            ["git", "init", "-q"],
            cwd=target_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode != 0:
            warn(
                f"git init 失败（exit {r.returncode}）：{r.stderr.strip() or '未知错误'}"
            )
            return
        r = subprocess.run(
            ["git", "add", "."],
            cwd=target_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if r.returncode != 0:
            warn(
                f"git add 失败（exit {r.returncode}）：{r.stderr.strip() or '未知错误'}"
            )
    except subprocess.TimeoutExpired:
        warn("git 命令超时，跳过")
    except Exception as e:  # noqa: BLE001  最后兜底，绝不静默
        warn(f"git 初始化出错：{type(e).__name__}: {e}")


# ---------- Main ----------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="初始化管理系统脚手架（默认 admin 模式：前后端 + PostgreSQL）"
    )
    parser.add_argument("project_name", help="项目名（kebab-case），如 my-app")
    parser.add_argument(
        "--only",
        choices=["admin", "ui", "server"],
        default=None,
        help="输出范围：默认 admin=前后端+中间件；ui=仅前端；server=仅后端",
    )
    parser.add_argument(
        "--title",
        dest="project_title",
        default=None,
        help="项目显示名（默认用项目名 Title-case 形式）",
    )
    parser.add_argument(
        "--admin-pass",
        default=None,
        help="初始管理员密码（默认随机生成，启动时控制台打印）",
    )
    parser.add_argument("--init-git", action="store_true", help="生成后自动 git init")
    parser.add_argument(
        "--with-redis",
        action="store_true",
        help="启用 Redis（限流/黑名单走 Redis 存储；默认无 Redis，走进程内内存）",
    )

    args = parser.parse_args()
    # 关键修复：之前用 str.isalnum() 允许所有 Unicode 字母（包括中文、emoji），
    # 这些字符进 PostgreSQL user/db 会失败（psycopg2 InvalidName / asyncpg 编码错）。
    # 改为严格的 ASCII 小写 + 数字 + - + _，与 Docker 容器名规则一致。
    if not re.match(r"^[a-z][a-z0-9_-]{0,62}$", args.project_name):
        print(
            "项目名只能以小写字母开头，由小写字母、数字、-、_ 组成，长度 1-63",
            file=sys.stderr,
        )
        return 1
    if args.project_name in {"admin", "server", "ui"}:
        print("项目名不能与 skill 模式同名（admin/server/ui）", file=sys.stderr)
        return 1

    # 防御性校验：title / admin_pass 不应包含会破坏 Python 源码或 shell 的字符
    # （这些值会插入到 .py docstring / .env / docker-compose.yml）
    for field_name, value in [
        ("project_title", args.project_title),
        ("admin_pass", args.admin_pass),
    ]:
        if value and any(c in value for c in ['"', "'", "\\", "\n", "\r", "\0"]):
            print(
                f"{field_name} 不能包含引号 / 反斜杠 / 换行等字符",
                file=sys.stderr,
            )
            return 1

    # 默认 admin 模式（最常见）
    if args.only is None:
        args.only = "admin"

    if args.project_title is None:
        args.project_title = (
            args.project_name.replace("-", " ").replace("_", " ").title()
        )
    args.admin_user = DEFAULT_ADMIN_USER
    if args.admin_pass is None:
        # 默认 admin/admin：本地开发最友好；用户生产前**必须**用 `--admin-pass` 改
        # 后端 lifespan + uvicorn 重启都会强警告，但用户明确选择不过度保护
        args.admin_pass = "admin"

    context = build_context(args)

    repo_root = Path(__file__).resolve().parent.parent
    templates_dir = repo_root / "templates"
    target_dir = Path.cwd() / args.project_name

    if target_dir.exists() or target_dir.is_symlink():
        if target_dir.is_symlink() and not target_dir.exists():
            # 破损 symlink — 直接报错，让用户清理
            print(f"❌ 目标已存在破损符号链接：{target_dir}", file=sys.stderr)
            return 1
        if target_dir.is_file():
            print(
                f"❌ 目标路径已存在且是文件（不是目录）：{target_dir}", file=sys.stderr
            )
            print("   请删除该文件或换一个项目名。", file=sys.stderr)
            return 1
        print(f"❌ 目标目录已存在：{target_dir}", file=sys.stderr)
        print("   如需覆盖请先删除目录，或换一个项目名。", file=sys.stderr)
        return 1

    # Jinja2 Environment：
    # - StrictUndefined：模板里写 {{ unknown }} 直接报错，避免静默生成空
    # - autoescape：对 .html / .vue 模板开启 HTML 转义，
    #   防止用户输入的 project_title / admin_pass 含 < > & 等被注入生成代码
    # - .py / .toml / .yml / .env 等代码模板仍保持原样输出（用 Markup 转义会破坏语法）
    def _select_autoescape(template_name: str | None) -> bool:
        return bool(template_name) and template_name.endswith((".html", ".htm", ".vue"))

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        autoescape=_select_autoescape,
        keep_trailing_newline=True,
        lstrip_blocks=False,
        trim_blocks=False,
    )

    print(f"🚀 正在生成项目：{args.project_name} -> {target_dir}（{args.only}）")

    target_dir.mkdir(parents=True)
    GENERATORS[args.only](target_dir, env, context, templates_dir)

    if args.only in ("admin", "server"):
        env_example = (
            target_dir / "backend" / ".env.example"
            if args.only == "admin"
            else target_dir / ".env.example"
        )
        if env_example.exists():
            env_target = (
                target_dir / "backend" / ".env"
                if args.only == "admin"
                else target_dir / ".env"
            )
            write_dotenv(env_target, env_example, context)

    if args.only in ("admin", "ui"):
        post_process_frontend(
            target_dir / "frontend" if args.only == "admin" else target_dir,
            context,
        )

    if args.init_git:
        init_git_safely(target_dir)

    print("✅ 项目生成完成！")
    print(f"   默认账号：{args.admin_user} / {args.admin_pass}")
    print(f"   后端地址：http://localhost:{DEFAULT_BACKEND_PORT}")
    # 安全提示：默认密码是 admin/admin，本地开发 OK，但生产前必须改
    if args.admin_pass == "admin":
        print()
        print("  ⚠️  ⚠️  ⚠️  生产环境安全警告 ⚠️  ⚠️  ⚠️")
        print("  当前默认密码 = 'admin'，仅供本地开发调试")
        print("  生产部署前**必须**用以下方式改成强密码：")
        print(
            f"    1. 重新跑：python scripts/init.py {args.project_name} --admin-pass '<强密码>'"
        )
        print("    2. 或编辑 .env 文件的 INITIAL_ADMIN_PASSWORD")
        print("    3. 后端会在 APP_ENV=prod 时**拒绝启动**（强密码检查）")
    print(f"   前端地址：http://localhost:{DEFAULT_FRONTEND_PORT}")
    if args.only == "admin":
        print()
        print("接下来（默认 PostgreSQL，中间件自动就绪）：")
        print(f"  cd {args.project_name}")
        print("  make install        # 装后端 + 前端依赖（首次）")
        print("  make backend-dev    # 终端 A：启动后端（自动复用本机 PG / 起 Docker）")
        print("  make frontend-dev   # 终端 B：启动前端")
    elif args.only == "server":
        print()
        print("接下来（默认 PostgreSQL，中间件自动就绪）：")
        print(f"  cd {args.project_name}")
        print("  make install        # 装后端依赖（首次）")
        print("  make backend-dev    # 启动后端（自动复用本机 PG / 起 Docker）")
    else:
        print()
        print("接下来：")
        print(f"  cd {args.project_name}")
        print("  pnpm install        # 或 npm install")
        print("  pnpm dev            # 启动开发服务器")
    return 0


if __name__ == "__main__":
    sys.exit(main())
