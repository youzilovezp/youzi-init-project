#!/usr/bin/env python3
"""
scaffold-init 初始化脚本。

设计原则：给非技术人员使用——CLI 越简单越好。
    python scripts/init.py my-app                  # 默认 admin 模式（前后端 + postgresql + redis）
    python scripts/init.py my-app --only ui        # 仅前端
    python scripts/init.py my-app --only server    # 仅后端

中间件 / 数据库 / 端口全部走 .env 或默认值，不再暴露 CLI 参数。

完整文档见 templates/skills/<mode>/SKILL.md。
"""

from __future__ import annotations

import argparse
import json
import os
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


# ---------- 默认值（业界惯例；非技术人员看一眼就懂） ----------
DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_PORT = 3000
DEFAULT_POSTGRES_PORT = 5432
DEFAULT_REDIS_PORT = 6379
DEFAULT_RABBITMQ_PORT = 5672
DEFAULT_RABBITMQ_MGMT_PORT = 15672
DEFAULT_MINIO_API_PORT = 9000
DEFAULT_MINIO_CONSOLE_PORT = 9001


# ---------- 中间件开关：从环境变量读（.env 中也可改） ----------
def _env_bool(name: str, default: bool) -> bool:
    """读 ENV 变量，true/1/yes/on 都算 True。"""
    val = os.environ.get(name, "").lower().strip()
    if val in ("true", "1", "yes", "on"):
        return True
    if val in ("false", "0", "no", "off"):
        return False
    return default


def _load_middleware_flags() -> dict:
    """中间件开关：默认 postgresql + redis，其他关闭。

    通过环境变量启用：
        ENABLE_RABBITMQ=true python scripts/init.py my-app
        ENABLE_MINIO=true ENABLE_CELERY=true python scripts/init.py my-app
    """
    return {
        "enable_redis": _env_bool("ENABLE_REDIS", True),
        "enable_rabbitmq": _env_bool("ENABLE_RABBITMQ", False),
        "enable_celery": _env_bool("ENABLE_CELERY", False),
        "enable_minio": _env_bool("ENABLE_MINIO", False),
    }


# ---------- Jinja context ----------
def build_context(args: argparse.Namespace, middleware: dict) -> dict:
    return {
        "project_name": args.project_name,
        "project_title": args.project_title,
        "secret_key": secrets.token_hex(32),
        # 数据库固定 postgresql（最通用）；如需 MySQL 修改 .env 的 DATABASE 字段
        "db_driver": "asyncpg",
        "database": "postgresql",
        "enable_i18n": True,  # 内置中文 locale，无需开关
        "only": args.only,
        **middleware,
        # 端口：业界惯例
        "backend_port": DEFAULT_BACKEND_PORT,
        "frontend_port": DEFAULT_FRONTEND_PORT,
        "postgres_port": DEFAULT_POSTGRES_PORT,
        "redis_port": DEFAULT_REDIS_PORT,
        "rabbitmq_port": DEFAULT_RABBITMQ_PORT,
        "rabbitmq_mgmt_port": DEFAULT_RABBITMQ_MGMT_PORT,
        "minio_api_port": DEFAULT_MINIO_API_PORT,
        "minio_console_port": DEFAULT_MINIO_CONSOLE_PORT,
        # admin 凭证
        "admin_user": args.admin_user,
        "admin_pass": args.admin_pass,
        "admin_email": DEFAULT_ADMIN_EMAIL,
        # 中间件密码（强随机，默认非技术用户无须关心）
        "db_password": secrets.token_urlsafe(20),
        "rabbitmq_password": secrets.token_urlsafe(20),
        "minio_user": f"minio-{secrets.token_hex(4)}",
        "minio_password": secrets.token_urlsafe(28),
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
        if rel in CONDITIONAL_TEMPLATES and not context.get(
            CONDITIONAL_TEMPLATES[rel], False
        ):
            return
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


def generate_server(
    target_dir: Path, env: Environment, context: dict, templates_dir: Path
) -> None:
    """server 模式：后端在项目根（与 SKILL.md 描述一致）。"""
    print("📦 模式：server（后端 + 中间件）")
    render_template(templates_dir / "backend", target_dir, env, context, templates_dir)
    render_template(templates_dir / "root", target_dir, env, context, templates_dir)


GENERATORS = {"admin": generate_admin, "ui": generate_ui, "server": generate_server}


CONDITIONAL_TEMPLATES = {
    "backend/app/tasks/celery_app.py.tmpl": "enable_celery",
}


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
def write_dotenv(target: Path, env_example: Path, secret_key: str) -> None:
    """把 .env.example 渲染后写入 .env，用真实 SECRET_KEY 替换占位符。"""
    content = env_example.read_text(encoding="utf-8").replace(
        "CHANGE_ME_TO_RANDOM_HEX", secret_key
    )
    target.write_text(content, encoding="utf-8")

    gitignore = target.parent.parent / ".gitignore"
    if gitignore.exists():
        gi = gitignore.read_text(encoding="utf-8")
        if ".env" not in gi.splitlines():
            gitignore.write_text(
                gi.rstrip() + "\n.env\n.env.*\n!.env.example\n", encoding="utf-8"
            )


def init_git_safely(target_dir: Path) -> None:
    """git init + git add .，.env 由 .gitignore 自动忽略。"""
    subprocess.run(["git", "init", "-q"], cwd=target_dir, check=False)
    subprocess.run(["git", "add", "."], cwd=target_dir, check=False)


# ---------- Main ----------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="初始化管理系统脚手架（默认 admin 模式，前后端 + postgresql + redis）"
    )
    parser.add_argument("project_name", help="项目名（kebab-case），如 my-app")
    parser.add_argument(
        "--only",
        choices=["admin", "ui", "server"],
        default="admin",
        help="输出范围：admin=前后端+中间件（默认）/ ui=仅前端 / server=仅后端",
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

    args = parser.parse_args()
    if not args.project_name.replace("-", "").replace("_", "").isalnum():
        print("项目名只能包含字母、数字、- 和 _", file=sys.stderr)
        return 1

    if args.project_title is None:
        args.project_title = (
            args.project_name.replace("-", " ").replace("_", " ").title()
        )
    args.admin_user = DEFAULT_ADMIN_USER
    if args.admin_pass is None:
        args.admin_pass = secrets.token_urlsafe(16)

    middleware = _load_middleware_flags()
    context = build_context(args, middleware)

    repo_root = Path(__file__).resolve().parent.parent
    templates_dir = repo_root / "templates"
    target_dir = Path.cwd() / args.project_name

    if target_dir.exists():
        print(f"❌ 目标目录已存在：{target_dir}", file=sys.stderr)
        print("   如需覆盖请先删除目录，或换一个项目名。", file=sys.stderr)
        return 1

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        lstrip_blocks=False,
        trim_blocks=False,
    )

    print(f"🚀 正在生成项目：{args.project_name} -> {target_dir}（{args.only}）")
    if middleware != {
        "enable_redis": True,
        "enable_rabbitmq": False,
        "enable_celery": False,
        "enable_minio": False,
    }:
        enabled = [k.replace("enable_", "") for k, v in middleware.items() if v]
        print(f"   启用中间件：{', '.join(enabled)}")

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
            write_dotenv(env_target, env_example, context["secret_key"])

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
    print(f"   前端地址：http://localhost:{DEFAULT_FRONTEND_PORT}")
    if args.only == "admin":
        print()
        print("接下来：")
        print(f"  cd {args.project_name}")
        print("  make start          # 启动所有中间件")
        print("  make backend-dev    # 终端 A：启动后端")
        print("  make frontend-dev   # 终端 B：启动前端")
    elif args.only == "server":
        print()
        print("接下来：")
        print(f"  cd {args.project_name}")
        print("  make start          # 启动中间件")
        print("  make install        # 安装后端依赖")
        print("  make backend-dev    # 启动后端开发服务器")
    else:
        print()
        print("接下来：")
        print(f"  cd {args.project_name}")
        print("  pnpm install        # 或 npm install")
        print("  pnpm dev            # 启动开发服务器")
    return 0


if __name__ == "__main__":
    sys.exit(main())
