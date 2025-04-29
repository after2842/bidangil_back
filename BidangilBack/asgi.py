"""
ASGI config for BidangilBack project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import BidangilBack.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BidangilBack.settings')

#application = get_asgi_application()


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            BidangilBack.routing.websocket_urlpatterns
        )
    ),
})