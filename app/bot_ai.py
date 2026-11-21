import random
from app.game_logic import LINES, free_cells, apply_move, check_winner

def _find_win(board: str, sym: str) -> int | None:
    for a, b, c in LINES:
        cells = [a, b, c]
        vals = [board[i] for i in cells]
        if vals.count(sym) == 2 and vals.count("_") == 1:
            return cells[vals.index("_")]
    return None

def _minimax(board: str, depth: int, is_max: bool, bot: str, human: str) -> int:
    result = check_winner(board)
    if result == bot: return 10 - depth
    if result == human: return depth - 10
    if result == "draw": return 0
    
    if is_max:
        best = -100
        for i in free_cells(board):
            best = max(best, _minimax(apply_move(board, i, bot), depth+1, False, bot, human))
        return best
    else:
        best = 100
        for i in free_cells(board):
            best = min(best, _minimax(apply_move(board, i, human), depth+1, True, bot, human))
        return best

def _best_minimax_move(board: str) -> int:
    best_score, best_move = -100, None
    for i in free_cells(board):
        score = _minimax(apply_move(board, i, "O"), 0, False, "O", "X")
        if score > best_score:
            best_score, best_move = score, i
    return best_move

def get_bot_move(board: str, level: int) -> int:
    cells = free_cells(board)
    if not cells:
        raise ValueError("Нет ходов")

    # level 2: средний (победа > блок > центр > угол > край)
    if level == 2:
        win = _find_win(board, "O")
        if win is not None: return win
        block = _find_win(board, "X")
        if block is not None: return block
        if 4 in cells: return 4
        corners = [i for i in (0,2,6,8) if i in cells]
        if corners: return random.choice(corners)
        return random.choice(cells)

    # level 3: сложный (минимакс с 15% ошибкой)
    if random.random() < 0.15:
        return random.choice(cells)
    return _best_minimax_move(board)
