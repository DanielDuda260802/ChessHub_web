from django.contrib import admin
from django.urls import path, include
from main.consumers import GameConsumer

# LOKALNI STORAGE
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/', include(('loginApp.urls', 'loginapp'), namespace='loginapp')),
]

# LOKALNI STORAGE
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # lokalni storage

websocket_urlpatterns = [
    path("ws/games/", GameConsumer.as_asgi()),
]


