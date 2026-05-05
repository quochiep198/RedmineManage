from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()

@router.get("/db")
async def check_db(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1 AS ok"))
    row = result.mappings().first()
    return {
        "database": "ok",
        "result": row["ok"] if row else None,
    }
