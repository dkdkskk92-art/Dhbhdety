from fastapi import Header, HTTPException
from telegram_init_data import validate, parse
from app.config import settings

async def get_tg_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("tma "):
        raise HTTPException(401, "Нет initData")
    
    init_data = authorization[4:]
    try:
        validate(init_data, settings.BOT_TOKEN)
        data = parse(init_data)
        return data["user"]
    except Exception:
        raise HTTPException(401, "Неверная подпись initData")
