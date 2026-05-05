from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from jose import jwt
from pydantic import BaseModel
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.middleware.auth import get_current_user
from app.middleware.ratelimit import login_limiter
from app.models.user import User

router = APIRouter()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def get_client_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def create_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "username": username,
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(payload: LoginRequest, response: Response, request: Request):
    ip = get_client_ip(request)

    if await login_limiter.is_locked(ip):
        ttl = login_limiter.ttl_remaining(ip)
        return JSONResponse(
            status_code=429,
            content={"detail": f"Too many failed attempts. Try again in {ttl} seconds."},
            headers={"Retry-After": str(ttl)},
        )

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == payload.username))
        user = result.scalar_one_or_none()

        if not user:
            await login_limiter.record_failure(ip)
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if not bcrypt.checkpw(payload.password.encode(), user.password.encode()):
            await login_limiter.record_failure(ip)
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if not user.is_active:
            await login_limiter.record_failure(ip)
            raise HTTPException(status_code=403, detail="Account is disabled")

        await login_limiter.reset(ip)

        token = create_token(user.id, user.username)

        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
        )

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "is_admin": user.is_admin,
            },
        }


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out"}


@router.get("/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return {"id": user.id, "username": user.username, "is_admin": user.is_admin}
