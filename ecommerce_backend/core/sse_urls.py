from django.urls import path
from core.sse import SSEConsumer, SSELiveConsumer

sse_urlpatterns = [
    path('<str:room_name>/', SSEConsumer.as_asgi()),
    path('', SSELiveConsumer.as_asgi()),
]

urlpatterns = []