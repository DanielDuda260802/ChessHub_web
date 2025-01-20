from celery import shared_task

import chess.pgn
import io
from .models import Game
from datetime import datetime

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

@shared_task
def process_pgn_file(pgn_content):
    """
    Task to split the PGN file into smaller chunks and delegate them for parallel processing.
    """
    pgn_io = io.StringIO(pgn_content)
    games = []
    chunk_size = 15  # Broj partija po zadatku
    chunk_count = 0

    while True:
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            break  # Prekid petlje kada više nema partija
        
        exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
        notation = game.accept(exporter)
        games.append(notation)

        # Ako imamo 15 partija, šaljemo ih na obradu
        if len(games) == chunk_size:
            process_pgn_chunk.delay(games)
            games = []
            chunk_count += 1

    # Obradi preostale partije koje nisu ispunile puni chunk
    if games:
        process_pgn_chunk.delay(games)
        chunk_count += 1

    return f'Submitted {chunk_count} chunks for processing (15 games each).'

@shared_task
def process_pgn_chunk(games):
    """
    Task to process a chunk of PGN games and store them in the database.
    """
    games_added = 0
    for pgn in games:
        pgn_io = io.StringIO(pgn)
        game = chess.pgn.read_game(pgn_io)
        if game.headers.get("Variant", "") == "Chess960":
            continue  # Preskačemo Chess960 partije

        game_data = {
            "site": game.headers.get("Site", ""),
            "date": parse_date(game.headers.get("Date", "")),
            "round": game.headers.get("Round", ""),
            "white_player": game.headers.get("White", ""),
            "black_player": game.headers.get("Black", ""),
            "result": game.headers.get("Result", ""),
            "white_elo": int(game.headers.get("WhiteElo", 0) or 0),
            "black_elo": int(game.headers.get("BlackElo", 0) or 0),
            "notation": pgn.strip(),
        }

        Game.objects.create(**game_data)
        games_added += 1

    return f'Chunk processed: {games_added} games added.'
