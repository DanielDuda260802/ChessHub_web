from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.core.files.storage import default_storage
from django.db.models import Q

from celery.result import AsyncResult

import chess
import chess.pgn
import io
import json
from chess.pgn import read_game
from io import StringIO

from main.models import Game
from .tasks import upload_pgn_to_storage
from .utils import get_games_by_fen

board = chess.Board()

game = chess.pgn.Game()
current_node = game

@login_required(login_url='login/')
def homepage(request):
    filters = request.session.get('filters', {
        'sort_by_date': '-date',
        'date_from': '',
        'date_to': '',
        'white_elo_filter': 'exact',
        'white_elo': '',
        'black_elo_filter': 'exact',
        'black_elo': '',
        'result': '',
    })

    # Zamijeni None vrijednosti s praznim stringovima kako bi se izbjegle greške u JS parsiranju
    filters = {key: value if value is not None else '' for key, value in filters.items()}
    
    # Pretvori filtere u JSON string i proslijedi u template sigurno
    filters_json = json.dumps(filters)

    return render(request, 'homepage.html', {'filters': filters_json})


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

            game_ids = get_games_by_fen(fen)
            print(f"backend vraća frontendu ažurirani fen: {fen} s ID-evima partija: {game_ids}")

            return JsonResponse({"fen": fen,"game_ids": list(game_ids)})
        except ValueError as e:
            return JsonResponse({"error": "Invalid move: " + str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": "An error occurred: " + str(e)}, status=500)


@csrf_exempt
def prev_move(request):
    global current_node
    if current_node.parent:
        current_node = current_node.parent
        board = current_node.board()
        fen = board.fen()
        game_ids = get_games_by_fen(fen)
        print(f"Vraćanje ispravnog FEN-a za prev_move sa backenda: {fen} s ID-evima partija: {game_ids}")
        return JsonResponse({"fen": fen, "pgn": str(game), "game_ids": list(game_ids)})
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
            
            game_ids = get_games_by_fen(fen)
            print(f"Vraćanje ispravnog FEN-a za next_move sa backenda: {fen} s ID-evima partija: {game_ids}")
            return JsonResponse({"fen": fen, "pgn": str(game), "game_ids": list(game_ids)})
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
            
def get_games(request):
    page = int(request.GET.get('page', 1))
    page_size = 100

    total_pages_key = 'games_total_pages'
    total_games = Game.objects.count()

    total_pages = (total_games // page_size) + (1 if total_games % page_size else 0)
    cache.set(total_pages_key, total_pages, 1200)
    print(f"[CACHE UPDATE] Total pages updated to {total_pages}")

    cache_key = f'games_page_{page}'
    cached_data = cache.get(cache_key)

    if page == 1 or not cached_data:
        print(f"[CACHE MISS] Fetching data from database for page {page}")
        games = Game.objects.all().order_by('id')
        paginator = Paginator(games, page_size)
        page_obj = paginator.get_page(page)

        games_list = list(page_obj.object_list.values(
            'id', 'white_player', 'white_elo', 'black_player', 'black_elo', 'result', 'date', 'site'
        ))

        response_data = {
            'games': games_list,
            'total_pages': total_pages,
            'current_page': page
        }

        cache.set(cache_key, response_data, 1200)
        return JsonResponse(response_data)

    print(f"[CACHE HIT] Returning cached data for page {page}")
    return JsonResponse(cached_data)

def game_details(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    try:
        pgn_stream = StringIO(game.notation)
        read_game(pgn_stream)  
    except Exception as e:
        raise ValueError(f"Invalid PGN notation: {str(e)}")

    context = {
        'game': game,
    }
    return render(request, 'game_details.html', context)

def get_game_moves(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    try:
        pgn_stream = StringIO(game.notation)
        loaded_game = read_game(pgn_stream)
        board = loaded_game.board()

        moves = []
        node = loaded_game
        while not node.is_end():
            next_node = node.variation(0)
            moves.append(board.san(next_node.move))
            board.push(next_node.move)
            node = next_node

        return JsonResponse({'moves': moves, 'result': game.result})
    except Exception as e:
        return JsonResponse({'error': f'Error reading game: {str(e)}'}, status=500)

def upload_pgn(request):
    if request.method == 'POST' and request.FILES.get('pgn_file'):
        pgn_file = request.FILES['pgn_file']
        file_path = f"pgn_uploads/{pgn_file.name}"

        saved_path = default_storage.save(file_path, pgn_file)
        upload_pgn_to_storage.apply_async(args=[saved_path])
        file_url = default_storage.url(saved_path)

        return JsonResponse({
            'success': True,
            'message': 'PGN file uploaded successfully.',
            'file_url': file_url
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})

def check_task_status(request, task_id):
    result = AsyncResult(task_id)
    response_data = {
        'task_id': task_id,
        'status': result.status,  
        'result': result.result   
    }
    return JsonResponse(response_data)

def refresh_game_cache():
    total_games = Game.objects.count()
    total_pages = (total_games // 100) + (1 if total_games % 100 else 0)
    cache.set('games_total_pages', total_pages, 1200)

def filtered_games(request):
    games = Game.objects.all()

    filters = request.GET.dict()
    if not filters and 'filters' in request.session:
        filters = request.session.get('filters')

    filters = {k: v if v is not None else '' for k, v in filters.items()}

    request.session['filters'] = filters
    request.session.modified = True

    if filters.get('date_from') and filters.get('date_to'):
        games = games.filter(date__range=[filters['date_from'], filters['date_to']])

    if filters.get('white_elo_filter') and filters.get('white_elo'):
        if filters['white_elo_filter'] == "exact":
            games = games.filter(white_elo=filters['white_elo'])
        elif filters['white_elo_filter'] == "gte":
            games = games.filter(white_elo__gte=filters['white_elo'])
        elif filters['white_elo_filter'] == "lte":
            games = games.filter(white_elo__lte=filters['white_elo'])

    if filters.get('black_elo_filter') and filters.get('black_elo'):
        if filters['black_elo_filter'] == "exact":
            games = games.filter(black_elo=filters['black_elo'])
        elif filters['black_elo_filter'] == "gte":
            games = games.filter(black_elo__gte=filters['black_elo'])
        elif filters['black_elo_filter'] == "lte":
            games = games.filter(black_elo__lte=filters['black_elo'])

    if filters.get('result'):
        games = games.filter(result=filters['result'])

    sort_by_date = filters.get('sort_by_date', '-date')
    games = games.order_by(sort_by_date)

    page_number = request.GET.get('page', 1)
    paginator = Paginator(games, 100)
    page_obj = paginator.get_page(page_number)

    games_list = list(page_obj.object_list.values('white_player', 'white_elo', 'black_player', 'black_elo', 'result', 'date', 'site'))

    return JsonResponse({
        'games': games_list,
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number
    })

@csrf_exempt
def clear_filters(request):
    if 'filters' in request.session:
        del request.session['filters']
    return JsonResponse({'status': 'success'})

