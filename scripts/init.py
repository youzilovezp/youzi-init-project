#!/usr/bin/env python3
"""
scaffold-init 初始化脚本

用法（三种模式）：
    python scripts/init.py <project-name> --only admin        # /yz:init-admin  完整前后端
    python scripts/init.py <project-name> --only ui           # /yz:init-ui     仅前端
    python scripts/init.py <project-name> --only server       # /yz:init-server 仅后端

示例：
    python scripts/init.py my-admin --only admin \\
        --backend fastapi --frontend vue3 --database postgresql \\
        --enable-redis --enable-celery

作用：
    1. 读取 templates/ 下的模板文件
    2. 用 Jinja2 替换占位变量（{{project_name}} 等）
    3. 根据 --only 输出到 <project-name>/ 的不同子目录
    4. 生成 .env 密钥、初始化 git 仓库（可选）
"""

from __future__ import annotations

import argparse
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError:
    print("缺少 jinja2，请执行：pip install jinja2")
    sys.exit(1)


# ---------- 模板上下文 ----------
def build_context(args: argparse.Namespace) -> dict:
    name = args.project_name
    title = name.replace("-", " ").replace("_", " ").title()
    return {
        "project_name": name,
        "project_title": title,
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
    }


# ---------- 模板渲染 ----------
def render_template(
    src: Path, dst: Path, env: Environment, context: dict, search_path: Path
) -> None:
    """递归渲染模板目录/文件。

    - 遇到目录：递归处理子项
    - 遇到 .tmpl 文件：去掉 .tmpl 后缀，用 Jinja2 渲染后写入
    - 其余文件：原样复制
    - 条件模板（CONDITIONAL_TEMPLATES 中声明）：开关为 false 时跳过
    """
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for child in src.iterdir():
            render_template(child, dst / child.name, env, context, search_path)
        return

    if src.suffix == ".tmpl":
        rel = str(src.relative_to(search_path))
        # 条件渲染：开关关闭时跳过
        if rel in CONDITIONAL_TEMPLATES and not context.get(
            CONDITIONAL_TEMPLATES[rel], False
        ):
            return
        target_path: Path = dst.with_suffix("")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        template = env.get_template(rel)
        target_path.write_text(template.render(**context), encoding="utf-8")
        return

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


# ---------- 各模式输出 ----------
def generate_admin(
    target_dir: Path, env: Environment, context: dict, templates_dir: Path
) -> None:
    """完整前后端：admin 模式。"""
    print("📦 模式：admin（完整前后端 + 中间件）")
    for sub in ("backend", "frontend"):
        render_template(
            templates_dir / sub, target_dir / sub, env, context, templates_dir
        )
    render_template(templates_dir / "root", target_dir, env, context, templates_dir)


def generate_ui(
    target_dir: Path, env: Environment, context: dict, templates_dir: Path
) -> None:
    """仅前端：ui 模式。"""
    print("📦 模式：ui（仅前端）")
    render_template(templates_dir / "frontend", target_dir, env, context, templates_dir)


def generate_server(
    target_dir: Path, env: Environment, context: dict, templates_dir: Path
) -> None:
    """后端 + 中间件：server 模式。"""
    print("📦 模式：server（后端 + 中间件）")
    render_template(templates_dir / "backend", target_dir, env, context, templates_dir)
    render_template(templates_dir / "root", target_dir, env, context, templates_dir)


GENERATORS = {
    "admin": generate_admin,
    "ui": generate_ui,
    "server": generate_server,
}


# ---------- 条件模板：未启用对应功能时不渲染 ----------
# 格式：相对 templates/ 的路径 -> 控制开关在 context 中的 key
CONDITIONAL_TEMPLATES = {
    "backend/app/tasks/celery_app.py.tmpl": "enable_celery",
}


# ---------- 主入口 ----------
def main() -> int:
    parser = argparse.ArgumentParser(description="初始化管理系统脚手架")
    parser.add_argument("project_name", help="项目名（kebab-case）")
    parser.add_argument(
        "--only",
        choices=["admin", "ui", "server"],
        default="admin",
        help="输出范围：admin=完整前后端 / ui=仅前端 / server=仅后端",
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

    args = parser.parse_args()
    if not args.project_name.replace("-", "").replace("_", "").isalnum():
        print("项目名只能包含字母、数字、- 和 _", file=sys.stderr)
        return 1

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
    )

    print(f"🚀 正在生成项目：{args.project_name} -> {target_dir}（{args.only}）")
    target_dir.mkdir(parents=True)

    # 调用对应模式的生成器
    GENERATORS[args.only](target_dir, env, context, templates_dir)

    # 写入 .env：admin 模式在后端子目录，server 模式在根目录
    backend_env_example = (
        target_dir / "backend" / ".env.example"
        if args.only == "admin"
        else target_dir / ".env.example"
    )
    if backend_env_example.exists():
        env_content = backend_env_example.read_text(encoding="utf-8").replace(
            "CHANGE_ME_TO_RANDOM_HEX", context["secret_key"]
        )
        env_target = (
            target_dir / "backend" / ".env"
            if args.only == "admin"
            else target_dir / ".env"
        )
        env_target.write_text(env_content, encoding="utf-8")
        # server 模式下，根 .env 已被 gitignore，无需额外处理

    if args.init_git:
        subprocess.run(["git", "init"], cwd=target_dir, check=False)
        subprocess.run(["git", "add", "."], cwd=target_dir, check=False)

    print("✅ 项目生成完成！")
    print()
    if args.only == "admin":
        print("接下来：")
        print(f"  cd {args.project_name}")
        print("  make start          # 启动所有中间件")
        print("  make backend-dev    # 终端 A：启动后端")
        print("  make frontend-dev   # 终端 B：启动前端")
    elif args.only == "server":
        print("接下来：")
        print(f"  cd {args.project_name}")
        print("  make start          # 启动中间件")
        print("  make install        # 安装后端依赖")
        print("  make backend-dev    # 启动后端开发服务器")
    else:
        print("接下来：")
        print(f"  cd {args.project_name}")
        print("  pnpm install        # 或 npm install")
        print("  pnpm dev            # 启动开发服务器")
    return 0


if __name__ == "__main__":
    sys.exit(main())
