from django.contrib import admin

from .models import Game, GameState

admin.site.register(Game)
admin.site.register(GameState)
