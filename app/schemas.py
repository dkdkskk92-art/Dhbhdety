from pydantic import BaseModel, Field

class GameState(BaseModel):
    game_id: int
    board: str
    turn: str
    status: str
    winner: str | None = None
    sparks: int
    room_code: str | None = None

class BotStartIn(BaseModel):
    level: int

class MoveIn(BaseModel):
    game_id: int
    index: int

class PvpJoinIn(BaseModel):
    room_code: str = Field(..., min_length=4, max_length=6)

# --- Схемы для Шахмат ---
class ChessJoinIn(BaseModel):
    room_code: str = Field(..., min_length=4, max_length=6)

class ChessMoveIn(BaseModel):
    game_id: int
    from_square: str
    to_square: str

class ChessMovesIn(BaseModel):
    game_id: int
    from_square: str
