"""Auth router: register, login, me, password reset."""
from fastapi import APIRouter
from fastapi_users import schemas
from pydantic import EmailStr
from app.core.auth import fastapi_users, auth_backend
from app.models.tables import User

router = APIRouter(prefix="/auth", tags=["auth"])

class UserRead(schemas.BaseUser[str]):
    full_name: str | None = None
    role: str = "legal"
    org_id: str | None = None

class UserCreate(schemas.BaseUserCreate):
    full_name: str | None = None
    role: str = "legal"
    org_id: str | None = None

class UserUpdate(schemas.BaseUserUpdate):
    full_name: str | None = None
    role: str | None = None
    org_id: str | None = None

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
)

router.include_router(
    fastapi_users.get_reset_password_router(),
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
)
