"""用户 CRUD。"""

from sqlalchemy import select

from app.core.security import hash_password, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserPasswordUpdate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_username(self, db, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return (await db.execute(stmt)).scalar_one_or_none()

    async def get_by_email(self, db, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return (await db.execute(stmt)).scalar_one_or_none()

    async def create(self, db, obj_in: UserCreate) -> User:
        data = obj_in.model_dump()
        password = data.pop("password")
        db_obj = User(**data, password_hash=hash_password(password))
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_password(
        self, db, user: User, payload: UserPasswordUpdate
    ) -> User:
        if not verify_password(payload.old_password, user.password_hash):
            raise ValueError("旧密码错误")
        user.password_hash = hash_password(payload.new_password)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


user_crud = CRUDUser(User)
