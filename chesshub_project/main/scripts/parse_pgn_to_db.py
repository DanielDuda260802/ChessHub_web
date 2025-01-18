import chess.pgn
import django
import os
from initialize_django import setup_django 
from datetime import datetime

setup_django()

from main.models import Game

def parse_pgn_and_store_in_db(pgn_file_path):
    with open(pgn_file_path, "r", encoding="ISO-8859-1") as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        while game:
            if game.headers.get("Variant", "") == "Chess960":
                print("Skipping Chess960 game.")
                game = chess.pgn.read_game(pgn_file)
                continue

            exporter = chess.pgn.StringExporter(headers=False, variations=False, comments=False)
            notation = game.accept(exporter)

            date = parse_date(game.headers.get("Date", ""))
            event_date = parse_date(game.headers.get("EventDate", ""))

            game_data = {
                "site": game.headers.get("Site", ""),
                "date": date,
                "round": game.headers.get("Round", ""),
                "white_player": game.headers.get("White", ""),
                "black_player": game.headers.get("Black", ""),
                "result": game.headers.get("Result", ""),
                "white_elo": game.headers.get("WhiteElo", None),
                "black_elo": game.headers.get("BlackElo", None),
                "white_title": game.headers.get("WhiteTitle", ""),
                "black_title": game.headers.get("BlackTitle", ""),
                "white_FideId": game.headers.get("WhiteFideId", None),
                "black_FideId": game.headers.get("BlackFideId", None),
                "eco": game.headers.get("ECO", ""),
                "event_date": event_date,
                "notation": notation.strip(),
            }

            Game.objects.create(**game_data)

            game = chess.pgn.read_game(pgn_file)

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


if __name__ == "__main__":
    import sys

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chesshub_project.settings")
    django.setup()

    if len(sys.argv) < 2:
        print("Koristite: python parse_pgn_to_db.py <pgn_file_path>")
    else:
        pgn_file_path = sys.argv[1]
        parse_pgn_and_store_in_db(pgn_file_path)
        print("PGN datoteka uspješno spremljena u bazu.")
