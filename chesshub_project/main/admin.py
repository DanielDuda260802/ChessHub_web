from django.contrib import admin
from .models import PGNFile, Game, FENPosition

# Register your models here.
admin.site.register(Game)
@admin.register(FENPosition)
class FENPositionAdmin(admin.ModelAdmin):
    list_display = ('fen_string', 'game', 'move_number', 'created_at')
admin.site.register