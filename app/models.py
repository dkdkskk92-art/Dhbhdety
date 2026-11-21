from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, Boolean, SmallInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class User(Base):
    __tablename__ = "users"
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sparks: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Game(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_code: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    game_type: Mapped[str] = mapped_column(String(20), default="tic_tac_toe") 
    player_x_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    player_o_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=True)
    
    board: Mapped[str] = mapped_column(String(150), default="_________") 
    turn: Mapped[str] = mapped_column(String(1), default="X") 
    status: Mapped[str] = mapped_column(String(10), default="playing") 
    winner: Mapped[str | None] = mapped_column(String(5), nullable=True)
    
    vs_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    bot_level: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
