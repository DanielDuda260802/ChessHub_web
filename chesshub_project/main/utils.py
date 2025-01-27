import redis
from django.conf import settings
from main.helper import sanitize_fen

redis_client = redis.Redis.from_url(settings.REDIS_URL)

def cache_fen_position(fen, game_id):
    sanitized_fen = sanitize_fen(fen)
    redis_key = f"fen:{sanitized_fen}"
    cache.lpush(redis_key, game_id)
    cache.expire(redis_key, 86400)

    print(f"Added game ID {game_id} to FEN {sanitized_fen}")


def get_games_by_fen(fen):
    redis_key = f"fen:{fen}"
    game_ids = redis_client.smembers(redis_key)

    return {int(game_id.decode('utf-8')) for game_id in game_ids}