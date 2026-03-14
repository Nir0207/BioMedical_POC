from abc import ABC, abstractmethod

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from biomedical_api.models.user import User, UserLoginAudit


class UserRepositoryProtocol(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def create_user(self, email: str, full_name: str, hashed_password: str) -> User:
        raise NotImplementedError

    @abstractmethod
    async def count_users(self) -> int:
        raise NotImplementedError


class UserRepository(UserRepositoryProtocol):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, email: str, full_name: str, hashed_password: str) -> User:
        user = User(email=email, full_name=full_name, hashed_password=hashed_password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def count_users(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(User))
        return int(result.scalar_one())


class LoginAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(self, user_id: int, success: bool, ip_address: str | None) -> UserLoginAudit:
        audit = UserLoginAudit(user_id=user_id, success=success, ip_address=ip_address)
        self.session.add(audit)
        await self.session.commit()
        await self.session.refresh(audit)
        return audit
