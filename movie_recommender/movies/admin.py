from django.contrib import admin
from .models import Movie, Genre, Review, UserMovie, Watchlist

# Регистрируем модели для отображения в админке
admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Review)
admin.site.register(UserMovie)
admin.site.register(Watchlist)
