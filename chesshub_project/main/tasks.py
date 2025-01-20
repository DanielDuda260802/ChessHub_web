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
    pgn_io = io.StringIO(pgn_content)
    game = chess.pgn.read_game(pgn_io)
    games_added = 0
    games_skipped = 0

    while game:
        if game.headers.get("Variant", "") == "Chess960":
            games_skipped += 1
            game = chess.pgn.read_game(pgn_io)
            continue

        exporter = chess.pgn.StringExporter(headers=False, variations=False, comments=False)
        notation = game.accept(exporter)

        game_data = {
            "site": game.headers.get("Site", ""),
            "date": parse_date(game.headers.get("Date", "")),
            "round": game.headers.get("Round", ""),
            "white_player": game.headers.get("White", ""),
            "black_player": game.headers.get("Black", ""),
            "result": game.headers.get("Result", ""),
            "white_elo": int(game.headers.get("WhiteElo", 0) or 0),
            "black_elo": int(game.headers.get("BlackElo", 0) or 0),
            "white_title": game.headers.get("WhiteTitle", ""),
            "black_title": game.headers.get("BlackTitle", ""),
            "white_FideId": int(game.headers.get("WhiteFideId", 0) or 0),
            "black_FideId": int(game.headers.get("BlackFideId", 0) or 0),
            "eco": game.headers.get("ECO", ""),
            "event_date": parse_date(game.headers.get("EventDate", "")),
            "notation": notation.strip(),
        }

        Game.objects.create(**game_data)
        games_added += 1
        game = chess.pgn.read_game(pgn_io)

    return f'PGN processed: {games_added} games added, {games_skipped} skipped (Chess960).'