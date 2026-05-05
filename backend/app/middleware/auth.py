from fastapi import HTTPException, Request
from jose import JWTError, jwt
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.user import User

ALGORITHM = "HS256"


def get_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get("access_token")


def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return {"id": int(payload["sub"]), "username": payload["username"]}
    except JWTError:
        return None


def optional_user(request: Request):
    token = get_token_from_cookie(request)
    if token:
        return verify_token(token)
    return None


def require_user(request: Request):
    token = get_token_from_cookie(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


async def get_current_user(request: Request) -> User:
    token = get_token_from_cookie(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_payload = verify_token(token)
    if not user_payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_payload["id"]))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user


async def require_admin(request: Request) -> User:
    user = await get_current_user(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user
