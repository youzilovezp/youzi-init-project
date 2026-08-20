"""菜单/权限 ORM 模型（用于前端动态路由）。"""

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_class import Base, TimestampMixin


class Menu(Base, TimestampMixin):
    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("menus.id", ondelete="CASCADE"), default=None
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    path: Mapped[str | None] = mapped_column(String(200))
    component: Mapped[str | None] = mapped_column(String(200))
    icon: Mapped[str | None] = mapped_column(String(50))
    sort: Mapped[int] = mapped_column(Integer, default=0)
    permission: Mapped[str | None] = mapped_column(String(100), index=True)
    type: Mapped[int] = mapped_column(
        Integer, default=2, comment="1=目录 2=菜单 3=按钮"
    )
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
