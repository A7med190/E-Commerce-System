import asyncio
import json
import logging
from typing import Dict, Set, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class WebSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = self.scope['url_route']['kwargs'].get('room_name', 'global')
        self.user = self.scope.get('user')
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"WebSocket connected: {self.channel_name} to {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected: {self.channel_name}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            elif message_type == 'subscribe':
                room = data.get('room')
                if room:
                    await self.channel_layer.group_add(room, self.channel_name)
                    await self.send(text_data=json.dumps({
                        'type': 'subscribed',
                        'room': room
                    }))
            elif message_type == 'unsubscribe':
                room = data.get('room')
                if room:
                    await self.channel_layer.group_discard(room, self.channel_name)
                    await self.send(text_data=json.dumps({
                        'type': 'unsubscribed',
                        'room': room
                    }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def broadcast_event(self, event):
        await self.send(text_data=json.dumps(event))


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope.get('user') or not self.scope['user'].is_authenticated:
            await self.close()
            return

        self.user_group = f"user_{self.scope['user'].id}"
        
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        await self.accept()
        logger.info(f"Notification WebSocket connected for user: {self.scope['user'].id}")

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def notify(self, event):
        await self.send(text_data=json.dumps(event['data']))

    async def order_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'data': event['data']
        }))

    async def product_alert(self, event):
        await self.send(text_data=json.dumps({
            'type': 'product_alert',
            'data': event['data']
        }))


class ChannelLayerManager:
    _instance: Optional['ChannelLayerManager'] = None
    
    def __init__(self):
        self.channel_layer = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_channel_layer(self):
        return self.channel_layer

    def set_channel_layer(self, layer):
        self.channel_layer = layer

    async def broadcast_to_group(self, group_name: str, event_type: str, data: dict):
        if self.channel_layer:
            await self.channel_layer.group_send(
                group_name,
                {
                    'type': event_type,
                    'data': data
                }
            )

    async def send_to_user(self, user_id: int, event_type: str, data: dict):
        if self.channel_layer:
            await self.channel_layer.group_send(
                f"user_{user_id}",
                {
                    'type': event_type,
                    'data': data
                }
            )

    async def broadcast_global(self, event_type: str, data: dict):
        if self.channel_layer:
            await self.channel_layer.group_send(
                "global",
                {
                    'type': event_type,
                    'data': data
                }
            )


channel_manager = ChannelLayerManager()
