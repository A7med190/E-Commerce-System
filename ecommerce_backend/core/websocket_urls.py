from django.urls import path
from core.websockets import WebSocketConsumer, NotificationConsumer

websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', WebSocketConsumer.as_asgi()),
    path('ws/notifications/', NotificationConsumer.as_asgi()),
    path('ws/', WebSocketConsumer.as_asgi()),
]

urlpatterns = []