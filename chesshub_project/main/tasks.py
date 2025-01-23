import logging
from celery import shared_task
import chess.pgn
import io
from .models import Game
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache
from django.core.files.storage import default_storage

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

@shared_task(queue='upload_queue')
def upload_pgn_to_storage(pgn_file_path):
    logger.info(f"Uploading PGN file to Azure Storage: {pgn_file_path}")

    try:
        if not default_storage.exists(pgn_file_path):
            logger.error(f"File not found: {pgn_file_path}")
            return f"File {pgn_file_path} not found"

        fetch_pgn_files_from_storage.apply_async()

        return f"File {pgn_file_path} uploaded and queued for processing."

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return f"Upload failed: {str(e)}"


@shared_task(queue='fetch_queue')
def fetch_pgn_files_from_storage():
    logger.info("Fetching PGN files from Azure Storage...")

    try:
        files = default_storage.listdir('pgn_uploads')[1]
        for file_name in files:
            file_path = f"{file_name}"
            process_pgn_queue.apply_async(args=[file_path])
            logger.info(f"Queued for processing: {file_path}")

    except Exception as e:
        logger.error(f"Error fetching PGN files: {str(e)}")


@shared_task(queue='process_queue')
def process_pgn_queue(pgn_file_path):
    logger.info(f"Processing PGN file with path: {pgn_file_path}")

    try:
        corrected_path = pgn_file_path.replace("pgn_uploads/pgn_uploads/", "pgn_uploads/")
        with default_storage.open(corrected_path, 'rb') as pgn_file:
            pgn_content = pgn_file.read().decode('ISO-8859-1')
        logger.info(f"Processing corrected PGN path: {corrected_path}")

        pgn_io = io.StringIO(pgn_content)
        games = []
        chunk_size = 15
        chunk_count = 0

        while True:
            game = chess.pgn.read_game(pgn_io)
            if game is None:
                break

            if game.headers.get("Variant", "") == "Chess960":
                logger.info("Skipping Chess960 game.")
                continue  

            exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
            notation = game.accept(exporter)
            games.append(notation)

            if len(games) == chunk_size:
                logger.info(f"Sending chunk {chunk_count + 1} to processing queue")
                process_pgn_chunk.apply_async(args=[games])
                games = []
                chunk_count += 1

        if games:
            logger.info("Sending final chunk to processing queue")
            process_pgn_chunk.apply_async(args=[games])
            chunk_count += 1

        logger.info(f"Total {chunk_count} chunks submitted for processing")

        move_processed_pgn_file(corrected_path)

    except Exception as e:
        logger.error(f"Error processing PGN file: {str(e)}")

@shared_task(queue='chunk_queue')
def process_pgn_chunk(games):
    logger.info(f"Processing chunk of {len(games)} games...")

    games_added = 0
    processed_games = []
    new_games = []

    for pgn in games:
        pgn_io = io.StringIO(pgn)
        game = chess.pgn.read_game(pgn_io)

        if game.headers.get("Variant", "") == "Chess960":
            logger.info("Skipping Chess960 game.")
            continue  

        new_games.append(Game(
            site=game.headers.get("Site", ""),
            date=parse_date(game.headers.get("Date", "")),
            round=game.headers.get("Round", ""),
            white_player=game.headers.get("White", ""),
            black_player=game.headers.get("Black", ""),
            result=game.headers.get("Result", ""),
            white_elo=int(game.headers.get("WhiteElo", 0) or 0),
            black_elo=int(game.headers.get("BlackElo", 0) or 0),
            notation=pgn.strip(),
        ))

        games_added += 1

        processed_games.append({
            "white_player": game.headers.get("White", ""),
            "white_elo": game.headers.get("WhiteElo", 0),
            "black_player": game.headers.get("Black", ""),
            "black_elo": game.headers.get("BlackElo", 0),
            "result": game.headers.get("Result", ""),
            "date": game.headers.get("Date", ""),
            "site": game.headers.get("Site", "")
        })

    if new_games:
        Game.objects.bulk_create(new_games, batch_size=500)
        games_added = len(new_games)
        logger.info(f"Stored {games_added} games in database.")

    update_cache_with_games(processed_games)
    broadcast_games(processed_games)

    logger.info(f"Broadcasting {len(processed_games)} new games to clients.")
    return f'Chunk processed: {games_added} games added and broadcasted.'

def move_processed_pgn_file(file_path):
    new_path = file_path.replace("pgn_uploads", "processed_pgns")
    default_storage.save(new_path, default_storage.open(file_path))
    default_storage.delete(file_path)
    logger.info(f"Moved processed file to: {new_path}")
