from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import chess
import chess.pgn
import io
import json

board = chess.Board()

game = chess.pgn.Game()
current_node = game

def homepage(request):
    return render(request, 'homepage.html')

@csrf_exempt
def add_move(request):
    global current_node
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            move_san = data.get("move")
            board = current_node.board()

            try:
                move = board.parse_san(move_san)
            except ValueError:
                return JsonResponse({"error": "Invalid move format"}, status=400)

            if move not in board.legal_moves:
                return JsonResponse({"error": "Illegal move"}, status=400)

            matching_variation = None
            for variation in current_node.variations:
                if variation.move == move:
                    matching_variation = variation
                    break

            if matching_variation:
                current_node = matching_variation
            else:
                current_node = current_node.add_variation(move)

            board.push(move)
            fen = board.fen()

            return JsonResponse({"fen": fen})
        except ValueError as e:
            return JsonResponse({"error": "Invalid move: " + str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": "An error occurred: " + str(e)}, status=500)

@csrf_exempt
def validate_move(request):
    global current_node
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            move_san = data.get("move")
            board = current_node.board()

            try:
                move = board.parse_san(move_san)
                if board.is_legal(move):
                    return JsonResponse({"valid": True})
                else:
                    return JsonResponse({"valid": False})
            except ValueError:
                return JsonResponse({"valid": False})

        except Exception as e:
            return JsonResponse({"valid": False, "error": str(e)}, status=400)

@csrf_exempt
def prev_move(request):
    global current_node
    if current_node.parent:
        current_node = current_node.parent
        board = current_node.board()
        fen = board.fen()
        return JsonResponse({"fen": fen, "pgn": str(game)})
    else:
        return JsonResponse({"error": "No previous move available"}, status=400)

@csrf_exempt
def next_move(request):
    global current_node
    if current_node.variations:
        if len(current_node.variations) == 1:
            current_node = current_node.variations[0]
            board = current_node.board()
            fen = board.fen()
            return JsonResponse({"fen": fen, "pgn": str(game)})
        else:
            variations = [str(variation.move) for variation in current_node.variations]
            print("Dostupne varijacije:", variations)
            return JsonResponse({"variations": variations})
    else:
        return JsonResponse({"error": "No next move available"}, status=400)

@csrf_exempt
def current_state(request):
    global current_node
    board = current_node.board()

    is_at_start = current_node.parent is None
    has_next_move = len(current_node.variations) > 0

    return JsonResponse({
        "is_at_start": is_at_start,
        "has_next_move": has_next_move
    })


@csrf_exempt
def choose_variation(request):
    global current_node
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            variation_index = int(data.get("variation_index", 0))
            print("Odabrana varijacija:", variation_index)

            if variation_index < len(current_node.variations):
                current_node = current_node.variations[variation_index]
                board = current_node.board()
                fen = board.fen()
                print("Varijacija odabrana i odigrana:", current_node.move)
                return JsonResponse({"fen": fen, "pgn": str(game)})
            else:
                print("Neispravan indeks varijacije:", variation_index)
                return JsonResponse({"error": "Invalid variation index"}, status=400)
        except Exception as e:
            print("Greška pri odabiru varijacije:", str(e))
            return JsonResponse({"error": str(e)}, status=400)
