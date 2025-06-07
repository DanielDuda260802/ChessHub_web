import torch
import chess
from main.model.model import ChessModel
from main.chess_model.auxiliary_func import board_to_matrix, index_to_move
from collections import Counter
import os

model_path = os.path.join(os.path.dirname(__file__), "..", "model", "best_model.pt")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = ChessModel()
model.load_state_dict(torch.load(model_path, map_location=device))
model.to(device)
model.eval()

game_history = []

def evaluate_fen(fen: str):
    global game_history

    print("📥 Received FEN:", fen)
    print("📚 Game history (last 8):", game_history[-8:])
    
    board = chess.Board(fen)
    history_boards = [chess.Board(f) for f in game_history[-8:]]

    rep_counter = Counter(game_history + [fen])

    board_tensor, meta = board_to_matrix(board, history_boards, rep_counter)
    board_tensor = torch.tensor(board_tensor, dtype=torch.float32).unsqueeze(0).to(device)
    meta_tensor = torch.tensor(meta, dtype=torch.float32).unsqueeze(0).to(device)

    # 🧾 Logovi za potvrdu
    print("🧮 Meta tensor:", meta_tensor.cpu().numpy().round(3).tolist())
    print("📐 Board tensor shape:", board_tensor.shape)
    print("📊 History boards FENs:")
    for i, b in enumerate(history_boards):
        print(f"  {i+1}. {b.fen()}")

    with torch.no_grad():
        policy_logits, value = model(board_tensor, meta_tensor)
        top_k = torch.topk(policy_logits, k=3, dim=1)
        top_indices = top_k.indices[0].cpu().numpy()
        top_moves = []

        for idx in top_indices:
            move = index_to_move(idx, board)
            if move != "invalid":
                top_moves.append(move.uci())

        eval_score = round(value.item(), 2)
        return {
            "eval": eval_score,
            "best_moves": top_moves
        }
