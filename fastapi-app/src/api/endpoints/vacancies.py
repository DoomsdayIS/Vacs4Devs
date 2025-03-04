from fastapi import APIRouter

from src import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/test1")
async def test1():
    return {"test1 endpoint": 200}
