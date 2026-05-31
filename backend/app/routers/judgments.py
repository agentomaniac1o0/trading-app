from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import TraderJudgmentCreate, TraderJudgmentResponse

router = APIRouter(prefix="/judgments", tags=["judgments"])


@router.get("/{symbol}", response_model=list[TraderJudgmentResponse])
async def get_judgments(symbol: str, db: AsyncSession = Depends(get_db)):
    return await crud.get_judgments(db, symbol.upper())


@router.post("", response_model=list[TraderJudgmentResponse])
async def save_judgments(
    data: list[TraderJudgmentCreate], db: AsyncSession = Depends(get_db)
):
    return await crud.create_judgments(db, data)
