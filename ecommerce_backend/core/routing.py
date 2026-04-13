from django.urls import re_path
from core.websockets import WebSocketConsumer, NotificationConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', WebSocketConsumer.as_asgi()),
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
    re_path(r'ws/$', WebSocketConsumer.as_asgi()),
]
