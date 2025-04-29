# yourproject/routing.py
from django.urls import re_path
from usrinfo.consumers import AvatarConsumer

websocket_urlpatterns = [
    re_path(r'^ws/avatars/$', AvatarConsumer.as_asgi()),
]