from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import engine, Base, get_db
from app.auth import get_tg_user
from app.models import Game
from app.services import (
    get_or_create_user, start_bot_game, player_move_bot, create_pvp, join_pvp, pvp_move,
    create_chess, join_chess, chess_move
)
from app.chess_logic import get_available_moves
from app.schemas import (
    GameState, BotStartIn, MoveIn, PvpJoinIn, ChessJoinIn, ChessMoveIn, ChessMovesIn
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Искры", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root(): return FileResponse("static/index.html")

@app.post("/api/auth")
async def auth(tg=Depends(get_tg_user), db: AsyncSession = Depends(get_db)):
    user = await get_or_create_user(db, tg["id"], tg.get("username"))
    return {"sparks": user.sparks, "username": user.username}

# --- Крестики-нолики API ---
@app.post("/api/game/bot", response_model=GameState)
async def start_bot(body: BotStartIn, tg=Depends(get_tg_user), db=Depends(get_db)):
    if body.level not in (2, 3): raise HTTPException(400, "level 2 или 3")
    user = await get_or_create_user(db, tg["id"], tg.get("username"))
    g = await start_bot_game(db, user, body.level)
    return GameState(game_id=g.id, board=g.board, turn=g.turn, status=g.status, winner=g.winner, sparks=user.sparks)

@app.post("/api/game/move", response_model=GameState)
async def move(body: MoveIn, tg=Depends(get_tg_user), db=Depends(get_db)):
    user = await get_or_create_user(db, tg["id"], tg.get("username"))
    try: g = await player_move_bot(db, user, body.game_id, body.index)
    except ValueError as e: raise HTTPException(400, str(e))
    await db.refresh(user)
    return GameState(game_id=g.id, board=g.board, turn=g.turn, status=g.status, winner=g.winner, sparks=user.sparks)

@app.post("/api/game/pvp/create")
async def pvp_create(tg=Depends(get_tg_user), db=Depends(get_db)):
    user = await get_or_create_user(db, tg["id"], tg.get("username"))
    g = await create_pvp(db, user)
    return {"game_id": g.id, "room_code": g.room_code, "expires_in": settings.PVP_WAIT_MINUTES * 60}

@app.post("/api/game/pvp/join")
async def pvp_join(body: PvpJoinIn, tg=Depends(get_tg_user), db=Depends(get_db)):
    user = await get_or_create_user(db, tg["id"], tg.get("username"))
    try: g = await join_pvp(db, user, body.room_code.upper())
    except ValueError as e: raise HTTPException(400, str(e))
    return {"game_id": g.id}

@app.get("/api/game/pvp/{game_id}", response_model=GameState)
async def pvp_state(game_id: int, tg=Depends(get_tg_user), db=Depends(get_db)):
    user = await get_or_create_user(db, tg["id"], tg.get("username"))
    g = await db.get(Game, game_id)
    if not g or user.telegram_id not in (g.player_x_id, g.player_o_id): raise HTTPException(404, "Игра не найдена")
    return GameState(game_id=g.id, board=g.board, turn=g.turn, status=g.status, winner=g.winner, sparks=user.sparks)

@app.post("/api/game/pvp/move", response_model=GameState)
async def pvp_move_ep(body: MoveIn, tg=Depends(get_tg_user), db=Depends(get_db)):
    user = await get_or_create_user(db, tg["id"], tg.get("username"))
    try: g = await pvp_move(db, user, body.game_id, body.index)
    except ValueError as e: raise HTTPException(400, str(e))
    await db.refresh(user)
    return GameState(game_id=g.id, board=g.board, turn=g.turn, status=g.status, winner=g.winner, sparks=user.sparks)

# --- Шахматы API ---
@app.post("/api/game/chess/create")
async def chess_create(tg=Depends(get_tg_user), db=Depends(get_db)):
    user = await get_or_create_user(db, tg["id"], tg.get("username"))
    g = await create_chess(db, user)
    return {"game_id": g.id, "room_code": g.room_code, "expires_in": settings.PVP_WAIT_MINUTES * 60}

@app.post("/api/game/chess/join")
async def chess_join(body: ChessJoinIn, tg=Depends(get_tg_user), db=Depends(get_db)):
    user = await get_or_create_user(db, tg["id"], tg.get("username"))
    try: g = await join_chess(db, user, body.room_code.upper())
    except ValueError as e: raise HTTPException(400, str(e))
    return {"game_id": g.id}

@app.post("/api/game/chess/moves", response_model=list[str])
async def chess_available_moves(body: ChessMovesIn, tg=Depends(get_tg_user), db=Depends(get_db)):
    game = await db.get(Game, body.game_id)
    if not game or game.game_type != "chess": raise HTTPException(404, "Игра не найдена")
    return get_available_moves(game.board, body.from_square)

@app.post("/api/game/chess/move")
async def chess_move_ep(body: ChessMoveIn, tg=Depends(get_tg_user), db=Depends(get_db)):
    user = await get_or_create_user(db, tg["id"], tg.get("username"))
    try: g = await chess_move(db, user, body.game_id, body.from_square, body.to_square)
    except ValueError as e: raise HTTPException(400, str(e))
    await db.refresh(user)
    return GameState(game_id=g.id, board=g.board, turn=g.turn, status=g.status, winner=g.winner, sparks=user.sparks)

@app.get("/health")
async def health(): return {"ok": True}
