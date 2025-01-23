from django.contrib import admin
from .models import PGNFile, Game, FENPosition

# Register your models here.
admin.site.register(Game)
admin.site.register(FENPosition)
admin.site.register(PGNFile)