from django.contrib import admin
from .models import PGNFile, Game

# Register your models here.
admin.site.register(Game)
admin.site.register(PGNFile)