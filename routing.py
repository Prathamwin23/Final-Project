from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/operations/', consumers.AgentConsumer.as_asgi()),
]