import redis
from django.conf import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL)

def cache_fen_position(fen, game_id):
    if game_id is None:
        print("Error: game_id is None, skipping Redis entry.")
        return

    redis_key = f"fen:{fen}"

    redis_client.sadd(redis_key, game_id)

    if redis_client.ttl(redis_key) == -1:
        redis_client.expire(redis_key, 86400)

    print(f"Added game ID {game_id} to FEN {fen}")

def get_games_by_fen(fen):
    redis_key = f"fen:{fen}"
    game_ids = redis_client.smembers(redis_key)

    return {int(game_id.decode('utf-8')) for game_id in game_ids}
