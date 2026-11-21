import random, string, asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Game
from app.game_logic import check_winner, apply_move
from app.bot_ai import get_bot_move
from app.chess_logic import get_initial_board, make_move as chess_make_move
from app.config import settings

def _code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

async def get_or_create_user(db: AsyncSession, tg_id: int, username: str | None) -> User:
    user = await db.get(User, tg_id)
    if not user:
        user = User(telegram_id=tg_id, username=username, sparks=settings.START_SPARKS)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user

async def _finish(db: AsyncSession, game: Game, winner: str, vs_pvp: bool, is_chess: bool = False):
    game.status = "finished"
    game.winner = winner
    
    if winner == "draw":
        await db.commit()
        return

    if is_chess:
        winner_id = game.player_x_id if winner == "X" else game.player_o_id
        loser_id = game.player_o_id if winner == "X" else game.player_x_id
        reward, penalty = 10, 5
    else:
        winner_id = game.player_x_id if winner == "X" else game.player_o_id
        loser_id = game.player_o_id if winner == "X" else game.player_x_id
        reward = 4 if vs_pvp else 2
        penalty = 2

    if winner_id:
        await db.execute(update(User).where(User.telegram_id == winner_id).values(sparks=User.sparks + reward))
    if loser_id:
        await db.execute(update(User).where(User.telegram_id == loser_id).values(sparks=User.sparks - penalty))
        await db.execute(update(User).where((User.telegram_id == loser_id) & (User.sparks < 0)).values(sparks=0))
    await db.commit()

# --- Логика Крестиков-Ноликов ---
async def start_bot_game(db, user: User, level: int) -> Game:
    game = Game(player_x_id=user.telegram_id, vs_bot=True, bot_level=level, status="playing", game_type="tic_tac_toe")
    db.add(game); await db.commit(); await db.refresh(game)
    return game

async def player_move_bot(db, user: User, game_id: int, index: int) -> Game:
    game = await db.get(Game, game_id)
    if not game or game.player_x_id != user.telegram_id or not game.vs_bot: raise ValueError("Игра не найдена")
    if game.status != "playing" or game.turn != "X": raise ValueError("Сейчас не ваш ход")
    
    game.board = apply_move(game.board, index, "X")
    res = check_winner(game.board)
    if res:
        await _finish(db, game, res, vs_pvp=False)
        return game
    
    game.turn = "O"
    await asyncio.sleep(1.0)
    
    bot_idx = get_bot_move(game.board, game.bot_level)
    game.board = apply_move(game.board, bot_idx, "O")
    res = check_winner(game.board)
    if res:
        await _finish(db, game, res, vs_pvp=False)
    else:
        game.turn = "X"
        await db.commit()
    return game

async def create_pvp(db, user: User) -> Game:
    game = Game(player_x_id=user.telegram_id, room_code=_code(), status="waiting", game_type="tic_tac_toe",
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.PVP_WAIT_MINUTES))
    db.add(game); await db.commit(); await db.refresh(game)
    return game

async def join_pvp(db, user: User, code: str) -> Game:
    game = (await db.execute(select(Game).where(Game.room_code == code, Game.status == "waiting", Game.game_type == "tic_tac_toe"))).scalar_one_or_none()
    if not game: raise ValueError("Комната не найдена или занята")
    if game.expires_at and game.expires_at < datetime.now(timezone.utc):
        game.status = "expired"; await db.commit(); raise ValueError("Время ожидания истекло")
    if game.player_x_id == user.telegram_id: raise ValueError("Нельзя играть с собой")
    
    game.player_o_id = user.telegram_id
    game.status = "playing"
    await db.commit(); await db.refresh(game)
    return game

async def pvp_move(db, user: User, game_id: int, index: int) -> Game:
    game = await db.get(Game, game_id)
    if not game or game.status != "playing" or game.game_type != "tic_tac_toe": raise ValueError("Игра не найдена")
    
    sym = "X" if user.telegram_id == game.player_x_id else "O"
    if game.turn != sym: raise ValueError("Не ваш ход")
    
    game.board = apply_move(game.board, index, sym)
    res = check_winner(game.board)
    if res:
        await _finish(db, game, res, vs_pvp=True)
    else:
        game.turn = "O" if sym == "X" else "X"
        await db.commit()
    return game

# --- Логика Шахмат ---
async def create_chess(db, user: User) -> Game:
    game = Game(player_x_id=user.telegram_id, room_code=_code(), status="waiting", game_type="chess",
                board=get_initial_board(), turn="X",
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.PVP_WAIT_MINUTES))
    db.add(game); await db.commit(); await db.refresh(game)
    return game

async def join_chess(db, user: User, code: str) -> Game:
    game = (await db.execute(select(Game).where(Game.room_code == code, Game.status == "waiting", Game.game_type == "chess"))).scalar_one_or_none()
    if not game: raise ValueError("Комната не найдена или занята")
    if game.expires_at and game.expires_at < datetime.now(timezone.utc):
        game.status = "expired"; await db.commit(); raise ValueError("Время ожидания истекло")
    if game.player_x_id == user.telegram_id: raise ValueError("Нельзя играть с собой")
    
    game.player_o_id = user.telegram_id
    game.status = "playing"
    await db.commit(); await db.refresh(game)
    return game

async def chess_move(db, user: User, game_id: int, from_sq: str, to_sq: str) -> Game:
    game = await db.get(Game, game_id)
    if not game or game.status != "playing" or game.game_type != "chess": raise ValueError("Игра не найдена")
    
    sym = "X" if user.telegram_id == game.player_x_id else "O"
    if game.turn != sym: raise ValueError("Не ваш ход")
    
    new_fen, result = chess_make_move(game.board, from_sq, to_sq)
    game.board = new_fen
    
    if result == "checkmate":
        await _finish(db, game, sym, vs_pvp=True, is_chess=True)
    elif result == "draw":
        await _finish(db, game, "draw", vs_pvp=True, is_chess=True)
    else:
        game.turn = "O" if sym == "X" else "X"
        await db.commit()
    return game
