from typing import Annotated

from fastapi import APIRouter, Depends, status

from biomedical_api.api.dependencies import get_auth_service, get_current_user_id, get_request_ip
from biomedical_api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from biomedical_api.schemas.user import UserResponse
from biomedical_api.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    user = await auth_service.register_user(payload.email, payload.full_name, payload.password)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    request_ip: Annotated[str | None, Depends(get_request_ip)],
) -> TokenResponse:
    token = await auth_service.authenticate(payload.email, payload.password, request_ip)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(
    user_id: Annotated[int, Depends(get_current_user_id)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    user = await auth_service.get_user(user_id)
    return UserResponse.model_validate(user)
