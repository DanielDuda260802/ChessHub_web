import logging
from celery import shared_task
import chess.pgn
import io
from .models import Game
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache

logger = logging.getLogger(__name__)

def parse_date(date_string):
    if not date_string or date_string == "?":
        return None
    try:
        return datetime.strptime(date_string, "%Y.%m.%d").date()
    except ValueError:
        pass
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        pass
    return None

@shared_task(queue='pgn_queue')
def process_pgn_file(pgn_content):
    logger.info("Starting PGN processing task...")
    
    pgn_io = io.StringIO(pgn_content)
    games = []
    chunk_size = 15
    chunk_count = 0

    while True:
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            break
        
        exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
        notation = game.accept(exporter)
        games.append(notation)

        if len(games) == chunk_size:
            logger.info(f"Sending chunk {chunk_count + 1} to processing queue")
            process_pgn_chunk.apply_async(args=[games], queue='chunk_queue')
            games = []
            chunk_count += 1

    if games:
        logger.info(f"Sending final chunk to processing queue")
        process_pgn_chunk.apply_async(args=[games], queue='chunk_queue')
        chunk_count += 1

    logger.info(f'Total {chunk_count} chunks submitted for processing')
    return f'Submitted {chunk_count} chunks for processing (15 games each).'

@shared_task(queue='chunk_queue')
def process_pgn_chunk(games):
    logger.info(f"Processing chunk of {len(games)} games...")

    games_added = 0
    processed_games = []

    for pgn in games:
        pgn_io = io.StringIO(pgn)
        game = chess.pgn.read_game(pgn_io)

        if game.headers.get("Variant", "") == "Chess960":
            logger.info("Skipping Chess960 game.")
            continue  

        game_instance = Game.objects.create(
            site=game.headers.get("Site", ""),
            date=parse_date(game.headers.get("Date", "")),
            round=game.headers.get("Round", ""),
            white_player=game.headers.get("White", ""),
            black_player=game.headers.get("Black", ""),
            result=game.headers.get("Result", ""),
            white_elo=int(game.headers.get("WhiteElo", 0) or 0),
            black_elo=int(game.headers.get("BlackElo", 0) or 0),
            notation=pgn.strip(),
        )

        games_added += 1

        processed_games.append({
            "id": game_instance.id,
            "white_player": game_instance.white_player,
            "white_elo": game_instance.white_elo,
            "black_player": game_instance.black_player,
            "black_elo": game_instance.black_elo,
            "result": game_instance.result,
            "date": str(game_instance.date),
            "site": game_instance.site
        })

    logger.info(f"Stored {games_added} games in database:")
    for game in processed_games:
        logger.info(game)

    update_cache_with_games(processed_games)

    broadcast_games(processed_games)

    logger.info(f"Broadcasting {len(processed_games)} new games to clients.")

    return f'Chunk processed: {games_added} games added and broadcasted.'

def update_cache_with_games(games):
    page_size = 100
    total_games = Game.objects.count()
    total_pages = (total_games // page_size) + (1 if total_games % page_size else 0)

    last_page_key = f'games_page_{total_pages}'
    last_page_data = cache.get(last_page_key, {'games': [], 'total_pages': total_pages, 'current_page': total_pages})

    if len(last_page_data['games']) + len(games) > page_size:
        total_pages += 1
        new_page_key = f'games_page_{total_pages}'
        cache.set(new_page_key, {'games': games, 'total_pages': total_pages, 'current_page': total_pages}, timeout=1200)
    else:
        last_page_data['games'].extend(games)
        cache.set(last_page_key, last_page_data, timeout=1200)

    first_page_key = "games_page_1"
    first_page_data = cache.get(first_page_key)
    if first_page_data:
        first_page_data['total_pages'] = total_pages  
        cache.set(first_page_key, first_page_data, timeout=1200)

    cache.set('games_total_pages', total_pages, timeout=1200)
    logger.info(f"Cache updated with {len(games)} new games on page {total_pages}")

def broadcast_games(processed_games):
    channel_layer = get_channel_layer()
    total_pages_key = 'games_total_pages'
    total_pages = cache.get(total_pages_key, 1)
    last_page_data = cache.get(f'games_page_{total_pages}', {"games": [], "current_page": total_pages})

    async_to_sync(channel_layer.group_send)(
        "games_group",
        {
            "type": "send_game_update",
            "data": last_page_data["games"]
        }
    )

    logger.info(f"Broadcasting {len(last_page_data['games'])} new games to clients on page {total_pages}")
