import pytest

from biomedical_api.repositories.user_repository import LoginAuditRepository, UserRepository
from biomedical_api.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_auth_service_registers_and_authenticates(reset_database) -> None:
    from biomedical_api.db.postgres import get_session_factory

    async with get_session_factory()() as session:
        service = AuthService(UserRepository(session), LoginAuditRepository(session))
        user = await service.register_user("service@example.com", "Service User", "strong-pass-123")
        token = await service.authenticate("service@example.com", "strong-pass-123", "127.0.0.1")

    assert user.email == "service@example.com"
    assert isinstance(token, str)
