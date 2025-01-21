import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache

logger = logging.getLogger(__name__)

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("games_group", self.channel_name)
        await self.accept()
        logger.info(f"Client connected: {self.channel_name}")

        total_pages_key = 'games_total_pages'
        total_pages = cache.get(total_pages_key, 1)
        last_page_data = cache.get(f'games_page_{total_pages}', {"games": []})

        await self.send(text_data=json.dumps({"games": last_page_data["games"], "current_page": total_pages}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("games_group", self.channel_name)
        logger.info(f"Client disconnected: {self.channel_name}")

    async def send_game_update(self, event):
        data = event["data"]
        logger.info(f"Sending game update to clients: {data}")

        await self.send(text_data=json.dumps({"games": data}))
