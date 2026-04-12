"""
ASGI config for pemon project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from core.routing import websocket_urlpatterns


settings_module = 'pemon.settings.production' if 'RENDER_EXTERNAL_HOSTNAME' in os.environ else 'pemon.settings.development'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(websocket_urlpatterns),
})
