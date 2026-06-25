from django.contrib import admin
from .models import Publisher, Game, GameKey

admin.site.register(Publisher)
admin.site.register(Game)
admin.site.register(GameKey)
