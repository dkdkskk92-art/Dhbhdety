LINES = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]

def check_winner(board: str) -> str | None:
    for a, b, c in LINES:
        if board[a] != "_" and board[a] == board[b] == board[c]:
            return board[a]
    if "_" not in board:
        return "draw"
    return None

def apply_move(board: str, index: int, symbol: str) -> str:
    if not (0 <= index <= 8):
        raise ValueError("Некорректная клетка")
    if board[index] != "_":
        raise ValueError("Клетка занята")
    return board[:index] + symbol + board[index+1:]

def free_cells(board: str) -> list[int]:
    return [i for i, ch in enumerate(board) if ch == "_"]
