from fastapi import HTTPException, status

from biomedical_api.core.security import create_access_token, hash_password, verify_password
from biomedical_api.models.user import User
from biomedical_api.repositories.user_repository import LoginAuditRepository, UserRepositoryProtocol


class AuthService:
    def __init__(self, user_repository: UserRepositoryProtocol, login_audit_repository: LoginAuditRepository) -> None:
        self.user_repository = user_repository
        self.login_audit_repository = login_audit_repository

    async def register_user(self, email: str, full_name: str, password: str) -> User:
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
        return await self.user_repository.create_user(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
        )

    async def authenticate(self, email: str, password: str, ip_address: str | None) -> str:
        user = await self.user_repository.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            if user:
                await self.login_audit_repository.record(user_id=user.id, success=False, ip_address=ip_address)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        await self.login_audit_repository.record(user_id=user.id, success=True, ip_address=ip_address)
        return create_access_token(str(user.id))

    async def get_user(self, user_id: int) -> User:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
