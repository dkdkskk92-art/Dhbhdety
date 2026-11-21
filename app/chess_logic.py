import chess

def get_initial_board() -> str:
    return chess.Board().fen()

def get_available_moves(fen: str, from_square: str) -> list[str]:
    board = chess.Board(fen)
    try:
        square = chess.parse_square(from_square)
        moves = [chess.square_name(move.to_square) for move in board.legal_moves if move.from_square == square]
        return moves
    except ValueError:
        return []

def make_move(fen: str, from_square: str, to_square: str) -> tuple[str, str | None]:
    board = chess.Board(fen)
    try:
        move_uci = f"{from_square}{to_square}"
        
        # Проверка на превращение пешки (автоматически ставим ферзя)
        piece = board.piece_at(chess.parse_square(from_square))
        if piece and piece.symbol().lower() == 'p':
            if to_square[1] in ['1', '8']:
                move_uci += 'q' 
                
        move = chess.Move.from_uci(move_uci)
        if move not in board.legal_moves:
            raise ValueError("Нелегальный ход")
        
        board.push(move)
        
        if board.is_checkmate():
            return board.fen(), "checkmate"
        elif board.is_game_over():
            return board.fen(), "draw"
            
        return board.fen(), None
    except Exception as e:
        raise ValueError(str(e))
