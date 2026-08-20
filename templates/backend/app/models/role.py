"""角色 ORM 模型。"""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_class import Base, TimestampMixin


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    remark: Mapped[str | None] = mapped_column(Text)

    users: Mapped[list["User"]] = relationship("User", back_populates="role")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Role id={self.id} code={self.code}>"
