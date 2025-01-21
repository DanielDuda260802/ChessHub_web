from django.contrib import admin
from django.urls import path, include
from main.consumers import GameConsumer

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/', include(('loginApp.urls', 'loginapp'), namespace='loginapp')),
]

websocket_urlpatterns = [
    path("ws/games/", GameConsumer.as_asgi()),
]