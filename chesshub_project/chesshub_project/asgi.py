import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chesshub_project.settings')

django_application = get_asgi_application()

from . import urls

application = ProtocolTypeRouter(
    {
    "http": ASGIStaticFilesHandler(django_application),  
    "websocket": AuthMiddlewareStack(URLRouter(urls.websocket_urlpatterns)),
    }
)
