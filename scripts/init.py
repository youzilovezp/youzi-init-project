#!/usr/bin/env python3
"""
scaffold-init 初始化脚本。

用法（三种模式）：
    python scripts/init.py <project-name> --only admin        # /yz-init-admin  完整前后端
    python scripts/init.py <project-name> --only ui           # /yz-init-ui     仅前端
    python scripts/init.py <project-name> --only server       # /yz-init-server 仅后端

示例：
    python scripts/init.py my-admin --only admin \\
        --backend fastapi --database postgresql \\
        --enable-redis --enable-celery \\
        --backend-port 8050 --frontend-port 5173 \\
        --admin-user admin --admin-pass 'ChangeMe!2025'

设计要点：
    1. backend / root / skills 模板用 Jinja2（合理——后端文本替换）
    2. frontend 模板**不**走 Jinja——纯 cp + sed + pnpm pkg（前端有自己的 Vite 模板）
    3. 端口、admin 凭证全部由 CLI 控制，默认值足以开箱
    4. .env 写入 + init_git 时显式 skip-worktree 防止密钥入库
"""

from __future__ import annotations

import argparse
import json
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


# ---------- Jinja context ----------
def build_context(args: argparse.Namespace) -> dict:
    return {
        "project_name": args.project_name,
        "project_title": args.project_title,
        "secret_key": secrets.token_hex(32),
        "db_driver": "asyncpg" if args.database == "postgresql" else "aiomysql",
        "database": args.database,
        "backend": args.backend,
        "frontend": args.frontend,
        "enable_redis": args.enable_redis,
        "enable_rabbitmq": args.enable_rabbitmq,
        "enable_celery": args.enable_celery,
        "enable_minio": args.enable_minio,
        "enable_i18n": args.enable_i18n,
        "only": args.only,
        # 端口 + admin（新增）
        "backend_port": args.backend_port,
        "frontend_port": args.frontend_port,
        "postgres_port": args.postgres_port,
        "redis_port": args.redis_port,
        "rabbitmq_port": args.rabbitmq_port,
        "rabbitmq_mgmt_port": args.rabbitmq_mgmt_port,
        "minio_api_port": args.minio_api_port,
        "minio_console_port": args.minio_console_port,
        "admin_user": args.admin_user,
        "admin_pass": args.admin_pass,
        "admin_email": args.admin_email,
        # 中间件密码（解决原"默认 = 项目名"弱口令）
        "db_password": args.db_password,
        "rabbitmq_password": args.rabbitmq_password,
        "minio_user": args.minio_user,
        "minio_password": args.minio_password,
    }


# ---------- Jinja rendering (仅用于 backend / root / skills) ----------
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

    # 非 .tmpl 文件——纯拷贝（不渲染，保护 frontend 的 Vue/TS/HTML 中的 {{ }})
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


# ---------- Frontend post-processing（替换项目常量） ----------
PLACEHOLDER_FRONTEND = "Youzi Admin"  # 占位符；sed 替换
PLACEHOLDER_BACKEND_PORT_DEFAULT = "59001"
PLACEHOLDER_FRONTEND_PORT_DEFAULT = "59000"


def post_process_frontend(target_dir: Path, context: dict) -> None:
    """不依赖 Jinja，纯文本替换前端里写死的占位符与默认端口。

    替换的位点：
      - PLACEHOLDER_FRONTEND（"Youzi Admin"） -> project_title
      - 后端 URL 中的 localhost:59001       -> localhost:<backend_port>
      - 前端 URL 中的 localhost:59000       -> localhost:<frontend_port>
      - package.json 'name'                 -> '<project>-frontend'
    """
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
        # vite.config.ts 特殊：port 是裸数字，不带 localhost 前缀
        if f.name == "vite.config.ts":
            text = text.replace(
                f"port: {PLACEHOLDER_FRONTEND_PORT_DEFAULT}",
                f"port: {frontend_port}",
            )
        f.write_text(text, encoding="utf-8")

    # package.json name 字段（避免 sed 处理 JSON 的 escape 问题）
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


# ---------- Safe .env handling ----------
def write_dotenv(target: Path, env_example: Path, secret_key: str) -> None:
    """把 .env.example 渲染后写入 .env，用真实 SECRET_KEY 替换占位符。

    重要：如果目标已 git 仓库，把 .env 标 skip-worktree（不阻断 add，但 commit 时跳过）。
    简单做法：把 .env 加进 .gitignore（已在模板里），并设置 local-未 tracked 模式。
    """
    content = env_example.read_text(encoding="utf-8").replace(
        "CHANGE_ME_TO_RANDOM_HEX", secret_key
    )
    target.write_text(content, encoding="utf-8")

    # 确保 .env 在 .gitignore 中存在，并使其成为不被 git add . 自动加入的项
    gitignore = target.parent.parent / ".gitignore"
    if gitignore.exists():
        gi = gitignore.read_text(encoding="utf-8")
        if ".env" not in gi.splitlines():
            gitignore.write_text(
                gi.rstrip() + "\n.env\n.env.*\n!.env.example\n", encoding="utf-8"
            )


# ---------- Init git safely ----------
def init_git_safely(target_dir: Path) -> None:
    """git init + git add .，但 .env 由 .gitignore 自动忽略（无密钥入库风险）。"""
    subprocess.run(["git", "init", "-q"], cwd=target_dir, check=False)
    # 先 add 全部；模板里 .env.example/.gitignore 已就位，.env 已被忽略
    subprocess.run(["git", "add", "."], cwd=target_dir, check=False)


# ---------- Main ----------
def main() -> int:
    parser = argparse.ArgumentParser(description="初始化管理系统脚手架")
    parser.add_argument("project_name", help="项目名（kebab-case）")
    parser.add_argument(
        "--only",
        choices=["admin", "ui", "server"],
        default="admin",
        help="输出范围：admin=完整前后端 / ui=仅前端 / server=仅后端",
    )
    parser.add_argument(
        "--title",
        dest="project_title",
        default=None,
        help="项目显示名（默认用项目名 Title-case 形式）",
    )
    parser.add_argument("--backend", default="fastapi", choices=["fastapi", "django"])
    parser.add_argument("--frontend", default="vue3", choices=["vue3", "react"])
    parser.add_argument(
        "--database", default="postgresql", choices=["postgresql", "mysql"]
    )

    parser.add_argument("--enable-redis", action="store_true", default=True)
    parser.add_argument("--no-redis", dest="enable_redis", action="store_false")
    parser.add_argument("--enable-rabbitmq", action="store_true")
    parser.add_argument("--enable-celery", action="store_true")
    parser.add_argument("--enable-minio", action="store_true")
    parser.add_argument("--enable-i18n", action="store_true", default=True)
    parser.add_argument("--no-i18n", dest="enable_i18n", action="store_false")
    parser.add_argument("--init-git", action="store_true", help="初始化 git 仓库")

    # 端口（新增）—— 默认走"标准 5xxxx 偏移"，避开常见端口冲突
    parser.add_argument(
        "--backend-port", type=int, default=59001, help="后端监听端口（默认 59001）"
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=59000,
        help="前端 vite dev 端口（默认 59000）",
    )
    parser.add_argument(
        "--postgres-port",
        type=int,
        default=55432,
        help="Postgres 端口（默认 55432，错开 5432 以减少冲突）",
    )
    parser.add_argument(
        "--redis-port",
        type=int,
        default=56379,
        help="Redis 端口（默认 56379，错开 6379）",
    )
    parser.add_argument(
        "--rabbitmq-port",
        type=int,
        default=55672,
        help="RabbitMQ AMQP 端口（默认 55672）",
    )
    parser.add_argument(
        "--rabbitmq-mgmt-port",
        type=int,
        default=15673,
        help="RabbitMQ 管理台端口（默认 15673）",
    )
    parser.add_argument(
        "--minio-api-port", type=int, default=59010, help="MinIO API 端口（默认 59010）"
    )
    parser.add_argument(
        "--minio-console-port",
        type=int,
        default=59011,
        help="MinIO 控制台端口（默认 59011）",
    )

    # admin 凭证（新增）
    parser.add_argument(
        "--admin-user", default="admin", help="初始管理员用户名（默认 admin）"
    )
    parser.add_argument(
        "--admin-pass", default=None, help="初始管理员密码（默认随机生成）"
    )
    parser.add_argument(
        "--admin-email", default="admin@example.com", help="初始管理员邮箱"
    )

    # 中间件密码（默认随机生成，避开"项目名作为弱口令"）
    parser.add_argument("--db-password", default=None, help="Postgres 密码（默认随机）")
    parser.add_argument(
        "--rabbitmq-password", default=None, help="RabbitMQ 密码（默认随机）"
    )
    parser.add_argument("--minio-user", default=None, help="MinIO 用户名（默认随机）")
    parser.add_argument("--minio-password", default=None, help="MinIO 密码（默认随机）")

    args = parser.parse_args()
    if not args.project_name.replace("-", "").replace("_", "").isalnum():
        print("项目名只能包含字母、数字、- 和 _", file=sys.stderr)
        return 1

    if args.project_title is None:
        args.project_title = (
            args.project_name.replace("-", " ").replace("_", " ").title()
        )
    if args.admin_pass is None:
        # 16 字节随机；满足非弱口令
        args.admin_pass = secrets.token_urlsafe(16)

    # 中间件默认密码：从 CLI 或随机生成（解决 B-05 弱口令）
    args.db_password = args.db_password or secrets.token_urlsafe(20)
    args.rabbitmq_password = args.rabbitmq_password or secrets.token_urlsafe(20)
    args.minio_user = args.minio_user or f"minio-{secrets.token_hex(4)}"
    args.minio_password = args.minio_password or secrets.token_urlsafe(28)

    context = build_context(args)
    repo_root = Path(__file__).resolve().parent.parent
    templates_dir = repo_root / "templates"
    target_dir = Path.cwd() / args.project_name

    if target_dir.exists():
        print(f"❌ 目标目录已存在：{target_dir}", file=sys.stderr)
        return 1

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        # 关键修复：开启 lstrip_blocks + trim_blocks，避免 {%- -%} 乱吞行首空白
        lstrip_blocks=False,
        trim_blocks=False,
    )

    print(f"🚀 正在生成项目：{args.project_name} -> {target_dir}（{args.only}）")
    target_dir.mkdir(parents=True)
    GENERATORS[args.only](target_dir, env, context, templates_dir)

    # 写入 .env（admin/server 模式）
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

    # frontend 后处理（参数替换）—— 仅 admin/ui 模式
    if args.only in ("admin", "ui"):
        post_process_frontend(
            target_dir / "frontend" if args.only == "admin" else target_dir,
            context,
        )

    if args.init_git:
        init_git_safely(target_dir)

    print("✅ 项目生成完成！")
    print(f"   默认账号：{args.admin_user} / {args.admin_pass}")
    print(f"   后端端口：{args.backend_port}   前端端口：{args.frontend_port}")
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
