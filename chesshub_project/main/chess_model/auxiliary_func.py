import numpy as np
import chess
from chess import Board
import json
from collections import Counter

def board_to_matrix(board: Board, history_boards, repetition_counter, T=8):
    # 1. Trenutna pozicija: figure (12) + legal moves (1)
    matrix = np.zeros((13, 8, 8), dtype=np.float32)

    # 1a. Figure encoding
    piece_map = board.piece_map()
    for square, piece in piece_map.items():
        row, col = divmod(square, 8)
        piece_type = piece.piece_type - 1
        piece_color = 0 if piece.color else 6
        matrix[piece_type + piece_color, row, col] = 1

    # 1b. Legal move destinations
    for move in board.legal_moves:
        row_to, col_to = divmod(move.to_square, 8)
        matrix[12, row_to, col_to] = 1

    # 2. REPEAT count planes (3 x 8x8)
    fen_key = board.board_fen()  # pozicija bez poteza i castlinga
    repetition_count = repetition_counter.get(fen_key, 0)
    repetition_planes = np.zeros((3, 8, 8), dtype=np.float32)
    for i in range(min(repetition_count, 3)):
        repetition_planes[i, :, :] = 1.0  # svi bitovi aktivni

    # 3. HISTORY planes (T zadnjih pozicija → 12 x T)
    history_planes = []
    for hist_board in history_boards[-T:]:
        hist_matrix = np.zeros((12, 8, 8), dtype=np.float32)
        piece_map = hist_board.piece_map()
        for square, piece in piece_map.items():
            row, col = divmod(square, 8)
            piece_type = piece.piece_type - 1
            piece_color = 0 if piece.color else 6
            hist_matrix[piece_type + piece_color, row, col] = 1
        history_planes.append(hist_matrix)

    if len(history_planes) < T:
        padding = [np.zeros((12, 8, 8), dtype=np.float32) for _ in range(T - len(history_planes))]
        history_planes = padding + history_planes

    history_tensor = np.concatenate(history_planes, axis=0)  # [12*T, 8, 8]

    # 4. META scalar podaci
    turn = 1.0 if board.turn == chess.WHITE else 0.0
    castling_rights = [
        float(board.has_kingside_castling_rights(chess.WHITE)),
        float(board.has_queenside_castling_rights(chess.WHITE)),
        float(board.has_kingside_castling_rights(chess.BLACK)),
        float(board.has_queenside_castling_rights(chess.BLACK)),
    ]
    en_passant = 1.0 if board.ep_square is not None else 0.0
    fullmove_number = board.fullmove_number / 100.0  # normirano

    meta = np.array(
        [turn] + castling_rights + [en_passant, fullmove_number],
        dtype=np.float32
    )

    # 5. Spajanje u jedan tenzor: [13 + 3 + 12*T, 8, 8]
    full_tensor = np.concatenate([matrix, repetition_planes, history_tensor], axis=0)

    return full_tensor, meta

def matrix_to_board(tensor, meta):
    board = chess.Board.empty()
    piece_planes = tensor[:12]

    for plane_idx in range(12):
        plane = piece_planes[plane_idx]
        indices = (plane == 1).nonzero(as_tuple=False)
        for idx in indices:
            row, col = idx.tolist()
            square = row * 8 + col
            piece_type = (plane_idx % 6) + 1
            color = plane_idx < 6
            piece = chess.Piece(piece_type, color)
            board.set_piece_at(square, piece)

    # Rekonstruiraj tko je na potezu
    board.turn = chess.WHITE if meta[0] == 1.0 else chess.BLACK

    # Castling prava
    if meta[1]: board.castling_rights |= chess.BB_H1  # White kingside
    if meta[2]: board.castling_rights |= chess.BB_A1  # White queenside
    if meta[3]: board.castling_rights |= chess.BB_H8  # Black kingside
    if meta[4]: board.castling_rights |= chess.BB_A8  # Black queenside

    # En passant
    board.ep_square = None  # Jednostavno ne možemo rekonstruirati točno polje

    # Fullmove broj (normirano u meta[6])
    board.fullmove_number = int(meta[6] * 100)

    return board

# Offseti za 8 pravaca (N, NE, E, SE, S, SW, W, NW)
DIRECTIONS = [
    (1, 0),    # N
    (1, 1),    # NE
    (0, 1),    # E
    (-1, 1),   # SE
    (-1, 0),   # S
    (-1, -1),  # SW
    (0, -1),   # W
    (1, -1),   # NW
]

# Konjski potezi (delta row, delta col)
KNIGHT_DIRS = [
    (2, 1), (1, 2), (-1, 2), (-2, 1),
    (-2, -1), (-1, -2), (1, -2), (2, -1)
]

# Promocije (osim dame)
PROMOTION_PIECES = {
    chess.KNIGHT: 0,
    chess.BISHOP: 1,
    chess.ROOK: 2,
}

def move_to_index(move: chess.Move, board: chess.Board) -> int:
    from_square = move.from_square
    to_square = move.to_square
    from_rank, from_file = divmod(from_square, 8)
    to_rank, to_file = divmod(to_square, 8)
    dx = to_file - from_file
    dy = to_rank - from_rank

    # 1️⃣ PROMOCIJE (64–72)
    if move.promotion in PROMOTION_PIECES:
        color = board.piece_at(from_square).color
        direction = 1 if color == chess.WHITE else -1
        rel_dir = (dy, dx)

        dir_map = {
            (direction, 0): 0,   # forward
            (direction, -1): 1,  # left
            (direction, 1): 2    # right
        }

        if rel_dir in dir_map:
            base_plane = 64 + PROMOTION_PIECES[move.promotion] * 3
            plane = base_plane + dir_map[rel_dir]
            return from_rank * 8 * 73 + from_file * 73 + plane

    # 2️⃣ Pravocrtni potezi (0–55)
    for dir_idx, (d_rank, d_file) in enumerate(DIRECTIONS):
        for dist in range(1, 8):
            if dy == d_rank * dist and dx == d_file * dist:
                plane = dir_idx * 7 + (dist - 1)
                return from_rank * 8 * 73 + from_file * 73 + plane

    # 3️⃣ Skok konjem (56–63)
    for knight_idx, (kdy, kdx) in enumerate(KNIGHT_DIRS):
        if dy == kdy and dx == kdx:
            plane = 56 + knight_idx
            return from_rank * 8 * 73 + from_file * 73 + plane

    raise ValueError(f"Move {move.uci()} cannot be encoded with AlphaZero move index.")

def index_to_move(index: int, board: chess.Board) -> chess.Move or str:
    from_square = index // 73
    plane = index % 73
    from_rank, from_file = divmod(from_square, 8)

    if plane < 56:
        # 1️⃣ Pravocrtni potezi
        dir_idx = plane // 7
        dist = (plane % 7) + 1
        d_rank, d_file = DIRECTIONS[dir_idx]
        to_rank = from_rank + d_rank * dist
        to_file = from_file + d_file * dist
        if not (0 <= to_rank < 8 and 0 <= to_file < 8):
            return "invalid"
        to_square = to_rank * 8 + to_file
        move = chess.Move(from_square, to_square)
        if move in board.legal_moves:
            return move

    elif 56 <= plane < 64:
        # 2️⃣ Skokovi konjem
        knight_idx = plane - 56
        kdy, kdx = KNIGHT_DIRS[knight_idx]
        to_rank = from_rank + kdy
        to_file = from_file + kdx
        if 0 <= to_rank < 8 and 0 <= to_file < 8:
            to_square = to_rank * 8 + to_file
            move = chess.Move(from_square, to_square)
            if move in board.legal_moves:
                return move

    elif 64 <= plane < 73:
        # 3️⃣ Promocije
        promo_offset = plane - 64
        piece_idx = promo_offset // 3
        dir_idx = promo_offset % 3
        direction = 1 if board.turn == chess.WHITE else -1
        dx = [0, -1, 1][dir_idx]
        dy = direction
        to_rank = from_rank + dy
        to_file = from_file + dx
        if 0 <= to_rank < 8 and 0 <= to_file < 8:
            to_square = to_rank * 8 + to_file
            promo_piece = list(PROMOTION_PIECES.keys())[piece_idx]
            move = chess.Move(from_square, to_square, promotion=promo_piece)
            if move in board.legal_moves:
                return move

    return "invalid"
