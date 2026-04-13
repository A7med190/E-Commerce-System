import asyncio
import json
import logging
from typing import Dict, Optional, Callable, Any
from functools import partial
from channels.generic.http import AsyncHttpConsumer
from django.http import StreamingHttpResponse

logger = logging.getLogger(__name__)


class SSEConsumer(AsyncHttpConsumer):
    channels: Dict[str, set] = {}
    event_handlers: Dict[str, Callable] = {}

    async def handle(self):
        await self.send_headers(headers_sent=False)
        
        room_name = self.scope['url_route']['kwargs'].get('room_name', 'default')
        
        if room_name not in self.channels:
            self.channels[room_name] = set()
        self.channels[room_name].add(self)

        try:
            while True:
                message = await asyncio.wait_for(
                    self.channel_layer.receive(f"sse_{room_name}"),
                    timeout=30.0
                )
                await self.send_body(f"data: {json.dumps(message)}\n\n".encode())
        except asyncio.TimeoutError:
            await self.send_body(b": heartbeat\n\n")
        except Exception as e:
            logger.error(f"SSE error for room {room_name}: {e}")
        finally:
            if room_name in self.channels:
                self.channels[room_name].discard(self)

    @classmethod
    async def broadcast(cls, room_name: str, event_type: str, data: Any):
        message = {'type': event_type, 'data': data}
        if cls.channel_layer:
            await cls.channel_layer.group_send(
                f"sse_{room_name}",
                {'type': 'sse_message', 'message': message}
            )

    @classmethod
    async def broadcast_all(cls, event_type: str, data: Any):
        message = {'type': event_type, 'data': data}
        for room_name in list(cls.channels.keys()):
            if cls.channel_layer:
                await cls.channel_layer.group_send(
                    f"sse_{room_name}",
                    {'type': 'sse_message', 'message': message}
                )


class SSELiveConsumer(AsyncHttpConsumer):
    async def handle(self):
        await self.send_headers(headers_sent=False)
        
        try:
            while True:
                await asyncio.sleep(30)
                await self.send_body(b": heartbeat\n\n")
        except Exception as e:
            logger.error(f"SSE live error: {e}")


class SSEPublisher:
    _instance: Optional['SSEPublisher'] = None

    def __init__(self):
        self.subscribers: Dict[str, set] = {}

    @classmethod
    def get_instance(cls) -> 'SSEPublisher':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, room: str, callback: Callable):
        if room not in self.subscribers:
            self.subscribers[room] = set()
        self.subscribers[room].add(callback)

    def unsubscribe(self, room: str, callback: Callable):
        if room in self.subscribers:
            self.subscribers[room].discard(callback)

    async def publish(self, room: str, event_type: str, data: Any):
        message = {'type': event_type, 'data': data, 'room': room}
        if room in self.subscribers:
            for callback in self.subscribers[room]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"SSE publish error: {e}")

    async def publish_all(self, event_type: str, data: Any):
        for room in list(self.subscribers.keys()):
            await self.publish(room, event_type, data)


sse_publisher = SSEPublisher()
