"""Dashboard 统计接口。"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.role import Role
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/overview", response_model=ResponseModel[dict], summary="总览统计")
async def overview(db: SessionDep, current_user: CurrentUser):  # 鉴权依赖
    """Dashboard 用的核心 KPI。"""
    _ = current_user  # 鉴权由 CurrentUser 依赖注入完成，函数体不使用
    user_total = (await db.execute(select(func.count(User.id)))).scalar_one()
    role_total = (await db.execute(select(func.count(Role.id)))).scalar_one()
    # 今日活跃：last 24h 内 updated_at 变动的用户（近似口径，可按需替换）
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    today_active = (
        await db.execute(select(func.count(User.id)).where(User.updated_at >= cutoff))
    ).scalar_one()

    return ResponseModel(
        data={
            "totalUsers": user_total,
            "totalRoles": role_total,
            "todayActive": today_active,
        }
    )
