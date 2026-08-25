#!/usr/bin/env python3
"""
重置管理员密码。

用法：
    # 生成新随机密码并打印
    python scripts/reset_admin.py

    # 指定新密码
    python scripts/reset_admin.py --password "NewPass!2025"

    # 重命名 admin 用户
    python scripts/reset_admin.py --username newadmin --password "NewPass!2025"
"""

import argparse
import asyncio
import secrets
import sys
from pathlib import Path

# 把 backend/ 加入 sys.path，让 `from app.xxx import` 可用
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.session import async_session  # noqa: E402
from app.models.user import User  # noqa: E402


async def main() -> int:
    parser = argparse.ArgumentParser(description="重置管理员密码")
    parser.add_argument(
        "--username",
        default=settings.INITIAL_ADMIN_USERNAME,
        help=f"管理员用户名（默认 {settings.INITIAL_ADMIN_USERNAME}）",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="新密码（不传则随机生成 16 位）",
    )
    args = parser.parse_args()

    # 防呆：--password 显式传空串会变成空密码。空密码过 bcrypt 仍然能写入，
    # 但用户登录会 401。直接拒绝。
    if args.password is not None and not args.password.strip():
        print("❌ --password 不能为空字符串（不传则随机生成 16 位）", file=sys.stderr)
        return 2

    new_password = args.password or secrets.token_urlsafe(16)

    async with async_session() as session:
        stmt = select(User).where(User.username == args.username)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            print(f"❌ 用户不存在：{args.username}")
            return 1
        user.password_hash = hash_password(new_password)
        user.is_active = True
        await session.commit()

    print("✅ 管理员密码已重置")
    print(f"   用户名：{args.username}")
    print(f"   新密码：{new_password}")
    print()
    print("⚠️  生产环境请立即修改后再次部署前重置。")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
