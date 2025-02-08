from django.contrib import admin
from .models import Movie, Genre, Review, Watchlist,Actor, MovieCredit, Person

# Регистрируем модели для отображения в админке
admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Review)
admin.site.register(Watchlist)
admin.site.register(Actor)
admin.site.register(MovieCredit)
admin.site.register(Person)
