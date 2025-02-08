from django.urls import path
from .views import recommend_movie
from . import views
from .views import movie_collections, actors_list, actor_detail

app_name = 'movies'

urlpatterns = [
    path('recommend/', views.recommend_movie, name='recommend_movie'),
    path('<int:movie_id>/', views.movie_detail, name='movie_detail'),  # Страница фильма
    path('<int:movie_id>/add_to_watchlist/', views.add_to_watchlist, name='add_to_watchlist'),
    path('<int:movie_id>/mark_as_watched/', views.mark_as_watched, name='mark_as_watched'),
    path('collections/', views.movie_collections, name='movie_collections'),
    path('actors/', actors_list, name='actors_list'),
    path('actors/<int:actor_id>/',  views.person_detail, name='person_detail'),
]